import sys
from pathlib import Path
from typing import Optional

from loguru import logger

_LOGS_DIR = Path("logs")
_LOGS_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
)
logger.add(
    _LOGS_DIR / "scraper.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    compression="zip",
)


def get_logger(name: Optional[str] = None):
    return logger.bind(name=name) if name else logger
