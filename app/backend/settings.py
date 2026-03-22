from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import CoreSettings

class BackendSettings(CoreSettings):
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    ADMIN_LOGIN: str
    ADMIN_PASSWORD: str

    MAIL: str = ""
    MAIL_PASSWORD: str = ""

    ALLOWED_HOSTS: list[str] = ["*"]


settings = BackendSettings()


engine = create_engine(settings.DATABASE_URL)

Base = automap_base()
Base.prepare(autoload_with=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()