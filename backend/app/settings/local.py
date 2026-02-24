from contextlib import asynccontextmanager

from elasticsearch import Elasticsearch  # type: ignore
from fastapi_mail import ConnectionConfig  # type: ignore
from redis.asyncio import Redis  # type: ignore
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.ext.automap import automap_base  # type: ignore
from sqlalchemy.orm import sessionmaker  # type: ignore

from ..settings.base import *  # noqa: F403

ALLOWED_HOSTS = ["*"]


# Main PG DB
DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "postgres")
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = int(os.getenv("DATABASE_PORT", 5432))
DATABASE_NAME = os.getenv("DATABASE_NAME", "my_database")

DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Redis settings
HOST_REDIS = os.getenv(
    "HOST_REDIS",
)
PORT_REDIS = os.getenv("PORT_REDIS")
DB_REDIS = os.getenv("DB_REDIS")


@asynccontextmanager
async def get_redis():
    redis_client = Redis(
        host=HOST_REDIS,
        port=PORT_REDIS,
        db=DB_REDIS,
        decode_responses=True,
    )
    try:
        yield redis_client
    finally:
        await redis_client.aclose()


# Scraper database settings
SCRAPER_DATABASE_USER = os.getenv("SCRAPER_DATABASE_USER")
SCRAPER_DATABASE_PASSWORD = os.getenv("SCRAPER_DATABASE_PASSWORD")
SCRAPER_DATABASE_HOST = os.getenv("SCRAPER_DATABASE_HOST")
SCRAPER_DATABASE_PORT = os.getenv("SCRAPER_DATABASE_PORT")
SCRAPER_DATABASE_NAME = os.getenv("SCRAPER_DATABASE_NAME")

SCRAPER_DATABASE_URL = f"postgresql://{SCRAPER_DATABASE_USER}:{SCRAPER_DATABASE_PASSWORD}@{SCRAPER_DATABASE_HOST}:{SCRAPER_DATABASE_PORT}/{SCRAPER_DATABASE_NAME}"

# Scraper PG
scraper_engine = create_engine(SCRAPER_DATABASE_URL)

ScraperBase = automap_base()
ScraperBase.prepare(autoload_with=scraper_engine)

ScraperSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=scraper_engine
)


def get_scraper_db():
    db = ScraperSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Mail settings
MAIL = os.getenv("MAIL", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")

MAIL_SETTINGS = (
    {
        "MAIL_USERNAME": MAIL,
        "MAIL_PASSWORD": MAIL_PASSWORD,
        "MAIL_FROM": MAIL,
        "MAIL_PORT": 587,
        "MAIL_SERVER": "smtp.gmail.com",
        "MAIL_STARTTLS": True,
        "MAIL_SSL_TLS": False,
        "USE_CREDENTIALS": True,
        "VALIDATE_CERTS": True,
    }
    if MAIL and MAIL_PASSWORD
    else {}
)

mail_conf = ConnectionConfig(**MAIL_SETTINGS)
