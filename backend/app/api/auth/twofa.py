import pyotp  # type: ignore
from jose import jwt, JWTError  # type: ignore
from datetime import datetime, timedelta

from backend.app.exceptions.token_exceptions import InvalidTokenException
from backend.app.settings import settings

SECRET = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM


def generate_otp_secret() -> str:
    return pyotp.random_base32()


def generate_otp_uri(email: str, secret: str, issuer: str = "LikeBus") -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def verify_otp_code(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code)


def create_temp_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "token_type": "temp",
        "exp": datetime.now() + timedelta(minutes=5),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


def decode_temp_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        if payload.get("token_type") != "temp":
            raise ValueError("Wrong token type")
        return payload["user_id"]
    except (JWTError, ValueError, KeyError):
        raise InvalidTokenException()
