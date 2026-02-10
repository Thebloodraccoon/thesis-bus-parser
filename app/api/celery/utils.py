from sqlalchemy.orm import Session  # type: ignore
from sqlalchemy import text  # type: ignore


def update_celery_cache(db: Session):
    db.execute(text("UPDATE celery_periodictaskchanged SET last_update = NOW()"))
    db.commit()
