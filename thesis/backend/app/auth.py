from datetime import datetime, timedelta, timezone
from typing import Union

import pyotp
from fastapi import Depends, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from thesis.backend.app.conf import get_db, settings
from thesis.backend.app.exceptions import (
    AdminAccessException,
    AnalyticsOrAdminAccessException,
    InvalidCodeException,
    InvalidTokenException,
    TokenBlacklistedException,
    UserNotFoundException,
)
from thesis.core.models import User
from thesis.backend.app.schemas import (
    TokenResponse,
    TwoFARequiredResponse,
    TwoFASetupResponse,
)

_ACCESS_TTL = timedelta(minutes=30)
_REFRESH_TTL = timedelta(days=30)
_TEMP_TTL = timedelta(minutes=5)
_ACCESS_TYPE = "access"
_REFRESH_TYPE = "refresh"
_TEMP_TYPE = "temp"


class AuthService:
    """Authentication service."""

    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @staticmethod
    def hash_password(plain: str) -> str:
        return AuthService._pwd_context.hash(plain)

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return AuthService._pwd_context.verify(plain, hashed)

    @staticmethod
    def _create_token(data: dict, token_type: str, ttl: timedelta) -> str:
        payload = {
            **data,
            "token_type": token_type,
            "exp": datetime.now(timezone.utc) + ttl,
        }
        return jwt.encode(
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def create_access_token(data: dict) -> str:
        return AuthService._create_token(data, _ACCESS_TYPE, _ACCESS_TTL)

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        return AuthService._create_token(data, _REFRESH_TYPE, _REFRESH_TTL)

    @staticmethod
    def create_temp_token(user_id: int) -> str:
        return AuthService._create_token({"user_id": user_id}, _TEMP_TYPE, _TEMP_TTL)

    @staticmethod
    def decode_token(token: str) -> dict:
        return jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

    @staticmethod
    def decode_temp_token(token: str) -> int:
        try:
            payload = AuthService.decode_token(token)
            if payload.get("token_type") != _TEMP_TYPE:
                raise ValueError("Wrong token type")
            return payload["user_id"]
        except (JWTError, ValueError, KeyError):
            raise InvalidTokenException()

    @staticmethod
    async def blacklist_token(token: str, exp: datetime) -> bool:
        async with settings.get_redis() as redis:
            ttl = int((exp - datetime.now(timezone.utc)).total_seconds())
            if ttl > 0:
                await redis.setex(f"blacklist:{token}", ttl, "blacklisted")
                return True
        return False

    @staticmethod
    async def is_blacklisted(token: str) -> bool:
        async with settings.get_redis() as redis:
            return bool(await redis.exists(f"blacklist:{token}"))

    @staticmethod
    def set_refresh_cookie(response: Response, token: str) -> None:
        response.set_cookie(
            key="refresh_token",
            value=token,
            httponly=True,
            samesite="none",
            secure=True,
            max_age=int(_REFRESH_TTL.total_seconds()),
        )

    @staticmethod
    def generate_otp_secret() -> str:
        return pyotp.random_base32()

    @staticmethod
    def generate_otp_uri(email: str, secret: str, issuer: str = "LikeBus") -> str:
        return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)

    @staticmethod
    def verify_otp(secret: str, code: str) -> bool:
        return pyotp.TOTP(secret).verify(code)

    @staticmethod
    def perform_login(
        user: User, db: Session, response: Response
    ) -> Union[TokenResponse, TwoFASetupResponse, TwoFARequiredResponse]:
        # Admin bypasses 2FA
        if user.email == settings.ADMIN_LOGIN:
            access = AuthService.create_access_token({"sub": user.email})
            AuthService.set_refresh_cookie(
                response, AuthService.create_refresh_token({"sub": user.email})
            )
            AuthService._update_last_login(user, db)
            return TokenResponse(access_token=access)

        # First login — setup TOTP
        if not user.is_2fa_enabled:
            if not user.otp_secret:
                user.otp_secret = AuthService.generate_otp_secret()
                db.commit()
            return TwoFASetupResponse(
                otp_uri=AuthService.generate_otp_uri(user.email, user.otp_secret),
                temp_token=AuthService.create_temp_token(user.id),
            )

        return TwoFARequiredResponse(temp_token=AuthService.create_temp_token(user.id))

    @staticmethod
    def finalize_2fa(
        otp_code: str, temp_token: str, db: Session, response: Response
    ) -> TokenResponse:
        user_id = AuthService.decode_temp_token(temp_token)
        user: User = db.get(User, user_id)
        if not user or not AuthService.verify_otp(user.otp_secret, otp_code):
            raise InvalidCodeException()

        if not user.is_2fa_enabled:
            user.is_2fa_enabled = True
            db.commit()

        AuthService._update_last_login(user, db)
        access = AuthService.create_access_token({"sub": user.email})
        AuthService.set_refresh_cookie(
            response, AuthService.create_refresh_token({"sub": user.email})
        )
        return TokenResponse(access_token=access)

    @staticmethod
    def _update_last_login(user: User, db: Session) -> None:
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)


async def _validate_token(
    token: HTTPAuthorizationCredentials, expected_type: str
) -> str:
    """Checks JWT: blacklist, token type, presence of sub."""
    if await AuthService.is_blacklisted(token.credentials):
        raise TokenBlacklistedException()

    try:
        payload = AuthService.decode_token(token.credentials)
    except JWTError:
        raise InvalidTokenException()

    email: str = payload.get("sub")
    if not email or payload.get("token_type") != expected_type:
        raise InvalidTokenException()

    return email


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db),
) -> type[User]:
    """FastAPI dependency: returns the currently authenticated user."""

    email = await _validate_token(token, _ACCESS_TYPE)

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise UserNotFoundException(email=email)

    return user


def admin_only(current_user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency: Allows access only to administrators."""

    if current_user.role != "admin":
        raise AdminAccessException()

    return current_user


def analytic_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency: allows access to analysts and administrators."""

    if current_user.role not in ("analytic", "admin"):
        raise AnalyticsOrAdminAccessException()

    return current_user


async def verify_refresh_token(token_str: str, db: Session) -> str:
    """Checks the refresh token and returns the user's email."""

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_str)

    email = await _validate_token(creds, _REFRESH_TYPE)
    if not db.query(User).filter(User.email == email).first():
        raise UserNotFoundException(email=email)

    return email
