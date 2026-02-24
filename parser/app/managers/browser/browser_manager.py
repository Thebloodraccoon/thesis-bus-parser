from contextlib import asynccontextmanager
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page

from parser.app.managers.http.proxy import ProxyManager
from parser.app.parsers.base_parser import BrowserParser
from parser.app.settings.exceptions import ParserConnectionException
from parser.app.settings.logger import get_logger

logger = get_logger(__name__)


class BrowserManager:
    """Manager of the browser for parsers"""

    def __init__(self, parser_class, use_proxy: bool = True):
        self.parser_class = parser_class
        self.proxy_manager = ProxyManager(use_proxy=use_proxy)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    @asynccontextmanager
    async def get_browser(self, headless: bool = True):
        """Context manager for obtaining a browser."""

        try:
            proxy = self.proxy_manager.get_proxy() if self.proxy_manager else None

            if isinstance(self.parser_class, BrowserParser):
                async with self.parser_class.setup_browser(
                    proxy, headless=headless
                ) as (browser, context):
                    self.browser = browser
                    self.context = context
                    logger.debug(f"Browser started for {self.parser_class.site.name}")
                    yield browser, context

        except Exception as e:
            logger.error(
                f"Failed to start browser for {self.parser_class.site.name}: {e}"
            )
            raise ParserConnectionException(f"Browser setup failed: {e}")
        finally:
            self.browser = None
            self.context = None

    async def create_page(self) -> Optional[Page]:
        """Creates a new page of the browser."""

        if not self.context:
            logger.warning("No browser context available")
            return None

        try:
            page = await self.context.new_page()
            logger.debug(f"New page created for {self.parser_class.site.name}")
            return page
        except Exception as e:
            logger.error(
                f"Failed to create page for {self.parser_class.site.name}: {e}"
            )
            return None

    async def close_page(self, page: Page):
        """Closes the page of the browser."""

        if page:
            try:
                await page.close()
                logger.debug(f"Page closed for {self.parser_class.site.name}")
            except Exception as e:
                logger.error(
                    f"Failed to close page for {self.parser_class.site.name}: {e}"
                )

    async def close_browser(self):
        """Closes the browser."""

        if self.context:
            try:
                await self.context.close()
                logger.debug(
                    f"Browser context closed for {self.parser_class.site.name}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to close browser context for {self.parser_class.site.name}: {e}"
                )

        if self.browser:
            try:
                await self.browser.close()
                logger.debug(f"Browser closed for {self.parser_class.site.name}")

            except Exception as e:
                logger.error(
                    f"Failed to close browser for {self.parser_class.site.name}: {e}"
                )
