from typing import Optional

from sqlalchemy import text

from app.parser.settings.conf import autocommit_engine
from app.parser.settings.logger import get_logger

logger = get_logger(__name__)


def update_if_changed(
    db_obj, new_data: dict, fields_to_update: Optional[list] = None
) -> bool:
    """Updates only specified fields of an SQLAlchemy object if they differ from the provided data."""

    updated = False

    for key, value in new_data.items():
        if fields_to_update and key not in fields_to_update:
            continue
        if getattr(db_obj, key) != value:
            setattr(db_obj, key, value)
            updated = True

    return updated


def optimize_postgres():
    """Executes VACUUM ANALYZE in a separate session (using AUTOCOMMIT)."""

    with autocommit_engine.connect() as connection:
        connection.execute(text("VACUUM ANALYZE routes"))
        logger.info("🔄 PostgreSQL optimized (VACUUM ANALYZE).")
