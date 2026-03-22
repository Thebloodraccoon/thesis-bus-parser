import os
import os
import sys
import time
from pathlib import Path
from typing import Optional

from loguru import logger

# Setting up a temporary zone
os.environ["TZ"] = "Europe/Kyiv"
time.tzset()

# Creation of a directory for logs
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)

logger.add(
    LOGS_DIR / "app.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    compression="zip",
)

# The path to the logs for compatibility
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
logs_dir = os.path.join(project_root, "logs")


def get_logger(name: Optional[str] = None):
    """He receives a logger with the specified name."""
    return logger.bind(name=name) if name else logger


def handle_processing_error(exception, departure_city, arrival_city, site_name):
    """Processing errors when processing routes."""

    exc_type = type(exception).__name__
    exc_msg = str(exception)

    if not exc_msg:
        error_info = f"{exc_type} (no detailed message)"
    else:
        error_info = f"{exc_type}: {exc_msg}"

    logger.error(
        f"Error processing route {departure_city.name_ua} -> {arrival_city.name_ua} | "
        f"{site_name}: {error_info}"
    )