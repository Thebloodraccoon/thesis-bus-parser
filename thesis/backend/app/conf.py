from contextlib import contextmanager, asynccontextmanager
from typing import Generator

from redis import asyncio as aioredis
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, sessionmaker
from thesis.core.config import CoreSettings


class Settings(CoreSettings):
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    ADMIN_LOGIN: str
    ADMIN_PASSWORD: str

    MAIL: str = ""
    MAIL_PASSWORD: str = ""

    ALLOWED_HOSTS: list[str] = ["*"]

    @asynccontextmanager
    async def get_redis(self):
        """Asynchronous context manager for Redis connections."""

        client = aioredis.from_url(self.REDIS_URL, decode_responses=True)
        try:
            yield client
        finally:
            await client.aclose()


settings = Settings()

engine = create_engine(settings.DATABASE_URL)

# automap_base for Celery-tables
AutomapBase = automap_base()
AutomapBase.prepare(autoload_with=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Contextual session DB manager for use in FastAPI Depends."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
