from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi.security import HTTPAuthorizationCredentials  # type: ignore
from jose import jwt  # type: ignore
from passlib.context import CryptContext  # type: ignore
from redis import Redis  # type: ignore

from app.backend.settings import settings, get_db

SECRET_KEY = settings.JWT_SECRET_KEY  # type: ignore
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_token(
    data: dict, token_type: str, expires_delta: Optional[timedelta]
) -> str:
    to_encode = data.copy()
    to_encode.update({"token_type": token_type})
    expire = datetime.now(timezone.utc) + expires_delta  # type: ignore
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: dict):
    return create_token(data, "access", timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(data: dict):
    return create_token(data, "refresh", timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


async def blacklist_token(token: str, expire_time: datetime):
    async with settings.get_redis() as redis:
        ttl = int((expire_time - datetime.now(timezone.utc)).total_seconds())
        if ttl > 0:
            await redis.setex(f"blacklist:{token}", ttl, "blacklisted")
            return True

        return False


async def is_token_blacklisted(token: str):
    async with settings.get_redis() as redis:
        return await redis.exists(f"blacklist:{token}")


def get_payload(token: HTTPAuthorizationCredentials):
    return jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
