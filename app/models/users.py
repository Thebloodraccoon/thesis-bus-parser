from datetime import datetime, timezone

from sqlalchemy import DateTime, Boolean  # type: ignore
from sqlalchemy import CheckConstraint, Column, Integer, String

from app.settings import settings


class User(settings.Base):  # type: ignore
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc))
    last_login = Column(DateTime)

    is_2fa_enabled = Column(Boolean, default=False, nullable=False)
    otp_secret = Column(String, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'polonus_manager', 'dps_manager')",
            name="check_user_role",
        ),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
