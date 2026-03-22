from typing import Optional

from app.parser.settings.logger import get_logger

logger = get_logger(__name__)


class ProxyManager:
    """Manager for working with proxy."""

    def __init__(self, use_proxy: bool = True):
        self._current_proxy = None
        self._use_proxy = use_proxy

    def get_proxy(self) -> Optional[str]:
        """Receives a proxy from the database."""

        if not self._use_proxy:
            logger.debug("Proxy disabled")
            return None

        try:
            return None

        except Exception as e:
            logger.error(f"Error getting proxy: {e}")
            return None

    def get_current_proxy(self) -> Optional[str]:
        """Returns the current proxy."""

        return self._current_proxy

    def clear_proxy(self):
        """Cleans the current proxy."""

        self._current_proxy = None
        logger.debug("Proxy cleared")
