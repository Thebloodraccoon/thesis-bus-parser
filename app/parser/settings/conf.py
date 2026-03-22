from contextlib import contextmanager
from typing import Generator

from fake_useragent import UserAgent  # type: ignore
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import Session, sessionmaker

from app.parser.settings.settings import settings

ua = UserAgent()

engine = create_engine(settings.DATABASE_URL)
autocommit_engine = create_engine(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
