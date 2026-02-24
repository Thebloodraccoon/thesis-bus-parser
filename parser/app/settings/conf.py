from contextlib import contextmanager
from typing import Generator

from fake_useragent import UserAgent  # type: ignore
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from parser.app.settings.constants import settings

ua = UserAgent()
engine = create_engine(settings.DATABASE_URL)
autocommit_engine = create_engine(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
