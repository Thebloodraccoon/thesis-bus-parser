from datetime import datetime

from sqlalchemy import Column, DateTime


class TimestampMixin:
    created_at = Column(
        DateTime, nullable=True, default=lambda: datetime.now(), index=True
    )
