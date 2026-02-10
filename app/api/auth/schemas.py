import re

from pydantic import BaseModel, field_validator

from app.exceptions.auth_exceptions import InvalidEmailException


class Login(BaseModel):
    email: str
    password: str

    @field_validator("email")
    def validate_email(cls, email):
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise InvalidEmailException()

        return email


class TokenResponse(BaseModel):
    access_token: str


class TwoFASetupResponse(BaseModel):
    otp_uri: str
    temp_token: str


class TwoFARequiredResponse(BaseModel):
    temp_token: str


class TwoFAVerifyRequest(BaseModel):
    otp_code: str
    temp_token: str


class LogoutResponse(BaseModel):
    detail: str
