from contextlib import asynccontextmanager

from ..settings.base import *  # noqa: F403
from redis.asyncio import Redis  # type: ignore
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import sessionmaker  # type: ignore

# Test Database settings
TEST_DATABASE_USER = "test_admin"
TEST_DATABASE_PASSWORD = "test_secret"  # nosec B105
TEST_DATABASE_HOST = os.getenv("TEST_DATABASE_HOST", "localhost")
TEST_DATABASE_PORT = 5432
TEST_DATABASE_NAME = "test_admin_panel"
DATABASE_URL = (
    f"postgresql://{TEST_DATABASE_USER}:{TEST_DATABASE_PASSWORD}@{TEST_DATABASE_HOST}:{TEST_DATABASE_PORT}/"
    f"{TEST_DATABASE_NAME}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Test Redis settings
TEST_HOST_REDIS = os.getenv("TEST_HOST_REDIS", "localhost")
TEST_PORT_REDIS = 6379
TEST_DB_REDIS = 0


@asynccontextmanager
async def get_redis():
    redis_client = Redis(
        host=TEST_HOST_REDIS,
        port=TEST_PORT_REDIS,
        db=TEST_DB_REDIS,
        decode_responses=True,
    )
    try:
        yield redis_client
    finally:
        await redis_client.aclose()
