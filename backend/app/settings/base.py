import os

from dotenv import load_dotenv  # type: ignore
from sqlalchemy.orm import declarative_base  # type: ignore

load_dotenv()
ALLOWED_HOSTS = ["*"]
Base = declarative_base()

# STAGE
STAGE = os.getenv("STAGE")
HOST = "0.0.0.0"  # nosec B104

# JWT settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Admin credentials
ADMIN_LOGIN = os.getenv("ADMIN_LOGIN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
