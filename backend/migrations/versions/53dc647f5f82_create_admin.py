"""create admin

Revision ID: 53dc647f5f82
Revises: 263f871074a9
Create Date: 2025-04-22 11:05:10.009576

"""
from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Integer
from sqlalchemy.sql import table, column

from backend.app.api.utils.auth_utils import get_password_hash
from backend.app.settings import settings

# revision identifiers, used by Alembic.
revision: str = '53dc647f5f82'
down_revision: Union[str, None] = '263f871074a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



users_table = table(
    "users",
    column("id", Integer),
    column("email", sa.String),
    column("hashed_password", sa.String),
    column("role", sa.String),
    column("created_at", sa.DateTime(timezone=True)),
    column("is_2fa_enabled", sa.Boolean),
    column("otp_secret", sa.String),
)

DEFAULT_ADMIN_EMAIL = settings.ADMIN_LOGIN
DEFAULT_ADMIN_PASSWORD = settings.ADMIN_PASSWORD


def upgrade() -> None:
    conn = op.get_bind()

    stmt = sa.text("SELECT id FROM users WHERE email = :email")
    admin_exists = conn.execute(stmt, {"email": DEFAULT_ADMIN_EMAIL}).fetchone() is not None

    if admin_exists:
        stmt = sa.text("""
            UPDATE users 
            SET hashed_password = :hashed_password,
                is_2fa_enabled = false,
                otp_secret = null
            WHERE email = :email
        """)

        conn.execute(
            stmt,
            {
                "email": DEFAULT_ADMIN_EMAIL,
                "hashed_password": get_password_hash(DEFAULT_ADMIN_PASSWORD)
            }
        )
    else:
        op.bulk_insert(
            users_table,
            [
                {
                    "email": DEFAULT_ADMIN_EMAIL,
                    "hashed_password": get_password_hash(DEFAULT_ADMIN_PASSWORD),
                    "role": "admin",
                    "created_at": datetime.now(),
                    "is_2fa_enabled": False,
                    "otp_secret": None
                }
            ],
        )


def downgrade() -> None:
    conn = op.get_bind()
    stmt = sa.text("DELETE FROM users WHERE email = :email")
    conn.execute(stmt, {"email": DEFAULT_ADMIN_EMAIL})