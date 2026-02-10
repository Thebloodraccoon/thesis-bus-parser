from typing import Union

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.auth.schemas import TwoFARequiredResponse, TwoFASetupResponse, TokenResponse, Login, TwoFAVerifyRequest, \
    LogoutResponse
from app.api.auth.utils import get_user, perform_login_logic, verify_2fa_and_finalize, verify_refresh_token, \
    get_current_user, logout_user, blacklist_refresh_token
from app.api.users.schemas import UserResponse
from app.api.utils.auth import verify_password, create_access_token
from app.exceptions.auth_exceptions import InvalidCredentialsException
from app.settings import settings

router = APIRouter()


@router.post(
    "/login",
    response_model=Union[TokenResponse, TwoFASetupResponse, TwoFARequiredResponse],
)
def login(request: Login, response: Response, db: Session = Depends(settings.get_db)):
    user = get_user(db, request.email)
    if not user or not verify_password(request.password, user.hashed_password):
        raise InvalidCredentialsException

    return perform_login_logic(user, db, response)


@router.post("/2fa/verify", response_model=TokenResponse)
def verify_2fa(
    request: TwoFAVerifyRequest,
    response: Response,
    db: Session = Depends(settings.get_db),
):
    return verify_2fa_and_finalize(request.otp_code, request.temp_token, db, response)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    request: Request,
    db: Session = Depends(settings.get_db),
):
    refresh_token = request.cookies.get("refresh_token", "")
    email = await verify_refresh_token(refresh_token, db)

    new_access_token = create_access_token(data={"sub": email})
    return {"access_token": new_access_token}


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    http_request: Request,
    response: Response,
    db: Session = Depends(settings.get_db),
    _: UserResponse = Depends(get_current_user),
):

    jwt_token = http_request.headers.get("Authorization").replace("Bearer ", "")
    logout_response = await logout_user(jwt_token, db)

    refresh_token = http_request.cookies.get("refresh_token", "")
    if refresh_token:
        await blacklist_refresh_token(refresh_token, db)

    response.delete_cookie(
        key="refresh_token", httponly=True, samesite="none", secure=True
    )

    return logout_response
