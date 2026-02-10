from datetime import datetime, timezone
from typing import Union

from fastapi import Depends, Response  # type: ignore
from fastapi.security import HTTPBearer  # type: ignore
from fastapi.security.http import HTTPAuthorizationCredentials  # type: ignore
from jose import JWTError  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.api.auth.schemas import TwoFASetupResponse, TokenResponse, TwoFARequiredResponse
from app.api.auth.twofa import (
    create_temp_token,
    generate_otp_uri,
    generate_otp_secret,
    decode_temp_token,
    verify_otp_code,
)
from app.api.users.schemas import UserResponse
from app.exceptions.auth_exceptions import AdminAccessException, InvalidCodeException
from app.exceptions.token_exceptions import (
    InvalidTokenException,
    TokenBlacklistedException,
)
from app.exceptions.user_exceptions import UserNotFoundException
from app.models.users import User
from app.settings import settings
from app.api.utils.auth import (
    blacklist_token,
    is_token_blacklisted,
    get_payload,
    create_access_token,
    create_refresh_token,
)

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_TYPE = "access"  # nosec
REFRESH_TOKEN_TYPE = "refresh"  # nosec


async def blacklist_jwt_token(
    token_str: str,
    expected_token_type: str,
    db: Session = Depends(settings.get_db),
):
    try:
        token = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_str)
        payload = get_payload(token)

        email: str = payload.get("sub")
        exp = payload.get("exp")
        token_type: str = payload.get("token_type")

        if token_type != expected_token_type:
            return None

        get_user(db, email)
        success = await blacklist_token(
            token.credentials, datetime.fromtimestamp(exp, tz=timezone.utc)
        )

        return success

    except JWTError:
        return False


async def logout_user(
    token_str: str,
    db: Session = Depends(settings.get_db),
):
    success = await blacklist_jwt_token(token_str, ACCESS_TOKEN_TYPE, db)

    if success:
        return {"detail": "Logout successful"}
    return {"detail": "Token already invalid"}


async def blacklist_refresh_token(
    token_str: str,
    db: Session = Depends(settings.get_db),
):
    return await blacklist_jwt_token(token_str, REFRESH_TOKEN_TYPE, db)


async def check_token(
    token: HTTPAuthorizationCredentials, required_token_type: str
) -> str:
    if await is_token_blacklisted(token.credentials):
        raise TokenBlacklistedException()

    payload = get_payload(token)
    email: str = payload.get("sub")
    token_type: str = payload.get("token_type")

    if email is None:
        raise InvalidTokenException()

    if token_type != required_token_type:
        raise InvalidTokenException()

    return email


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(settings.get_db),
) -> User:
    try:
        email = await check_token(token, ACCESS_TOKEN_TYPE)
    except JWTError:
        raise InvalidTokenException()

    user = get_user(db, email)
    if user is None:
        raise UserNotFoundException(email=email)

    return user


async def verify_refresh_token(
    token_str: str,
    db: Session = Depends(settings.get_db),
) -> str:
    try:
        token = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_str)
        email = await check_token(token, REFRESH_TOKEN_TYPE)

        user = get_user(db, email)
        if not user:
            raise UserNotFoundException()

        return email

    except JWTError:
        raise InvalidTokenException()


def admin_only(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    if current_user.role != "admin":
        raise AdminAccessException()

    return current_user


def get_user(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user

    raise UserNotFoundException(email=email)


def update_last_login(db: Session, user: User):
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)


def create_tokens(
    email: str,
    response: Response,
):
    access_token = create_access_token(data={"sub": email})
    refresh_token = create_refresh_token(data={"sub": email})

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="none",
        secure=True,
        max_age=30 * 24 * 60 * 60,
    )
    return access_token, refresh_token


def perform_login_logic(
    user: User, db: Session, response: Response
) -> Union[TokenResponse, TwoFASetupResponse, TwoFARequiredResponse]:
    if user.email == settings.ADMIN_LOGIN:
        access_token, refresh_token = create_tokens(user.email, response)
        update_last_login(db, user)

        return TokenResponse(access_token=access_token)

    if not user.is_2fa_enabled:
        if not user.otp_secret:
            user.otp_secret = generate_otp_secret()
            db.commit()

        return TwoFASetupResponse(
            otp_uri=generate_otp_uri(user.email, user.otp_secret),
            temp_token=create_temp_token(user.id),
        )

    return TwoFARequiredResponse(temp_token=create_temp_token(user.id))


def verify_2fa_and_finalize(
    otp_code: str, temp_token: str, db: Session, response: Response
) -> dict:
    user_id = decode_temp_token(temp_token)
    user = db.get(User, user_id)

    if not user or not verify_otp_code(user.otp_secret, otp_code):
        raise InvalidCodeException

    if not user.is_2fa_enabled:
        user.is_2fa_enabled = True
        db.commit()

    update_last_login(db, user)

    access_token, refresh_token = create_tokens(user.email, response)
    return {"access_token": access_token}
