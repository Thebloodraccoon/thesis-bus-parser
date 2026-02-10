from contextlib import contextmanager, asynccontextmanager
from typing import Generator

import Redis
from fake_useragent import UserAgent  # type: ignore
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.settings.constants import settings

ua = UserAgent()
engine = create_engine(settings.DATABASE_URL)  # type: ignore
autocommit_engine = create_engine(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")  # type: ignore

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def get_redis():
    redis_client = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,
    )
    try:
        yield redis_client
    finally:
        await redis_client.aclose()


MAIL_SETTINGS = (
    {
        "MAIL_USERNAME": settings.MAIL,
        "MAIL_PASSWORD": settings.MAIL_PASSWORD,
        "MAIL_FROM": settings.MAIL,
        "MAIL_PORT": 587,
        "MAIL_SERVER": "smtp.gmail.com",
        "MAIL_STARTTLS": True,
        "MAIL_SSL_TLS": False,
        "USE_CREDENTIALS": True,
        "VALIDATE_CERTS": True,
    }
    if settings.MAIL and settings.MAIL_PASSWORD
    else {}
)