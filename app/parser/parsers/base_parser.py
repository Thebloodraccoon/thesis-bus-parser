from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime
from logging import WARNING
from typing import Any, Dict, List

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright
from pydantic import ValidationError
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from app.core.models import SiteModel
from app.parser.db.city_db import logger
from app.parser.managers.http import send_request, get_response_size
from app.parser.schemas.city_schema import CitySchema
from app.parser.schemas.route_schema import RouteSchema
from app.parser.schemas.ticket_schema import TicketDataSchema
from app.parser.schemas.trip_history_schema import TripHistorySchema
from app.parser.schemas.trip_schema import TripSchema
from app.parser.settings.conf import ua, get_db


class ProxyConnectionError(Exception):
    pass


class CityNotFoundError(Exception):
    """Custom exception for when a city is not found in dropdown suggestions."""

    pass


async def allow_only_needed_requests(page):
    allowed_domains = ["busfor.ua"]
    allowed_resource_types = ["xhr", "script", "document"]

    async def handle_route(route, request):
        if (
            any(domain in request.url for domain in allowed_domains)
            and request.resource_type in allowed_resource_types
        ):
            await route.continue_()
            return

        await route.abort()

    await page.route("**/*", handle_route)


async def block_unnecessary_resources(page):
    blocked_resource_types = ["image", "stylesheet", "font", "xhr", "media", "other"]
    blocked_extensions = [
        ".svg",
        ".ico",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ttf",
        ".woff",
        ".woff2",
        ".eot",
    ]

    async def handle_route(route, request):
        if request.resource_type in blocked_resource_types:
            if request.resource_type == "xhr" and not any(
                ext in request.url for ext in blocked_extensions
            ):
                await route.continue_()
                return
            await route.abort()
            return

        if any(request.url.endswith(ext) for ext in blocked_extensions):
            await route.abort()
            return

        await route.continue_()

    await page.route("**/*", handle_route)


async def block_third_party_requests(page):
    async def handle_route(route, request):
        domains = ["busfor.ua"]
        if any(domain in request.url for domain in domains):
            await route.continue_()
            return

        try:
            parsed_url = request.url.split("/")[2]
            if parsed_url in ["34.160.229.191"]:
                await route.continue_()
                return
        except Exception as e:
            logger.error(f"Error while processing request URL: {request.url} - {e}")
            pass

        await route.abort()

    await page.route("**/*", handle_route)


async def initialize_browser(headless: bool):
    """Helper method for initializing the browser with retry support."""
    try:
        playwright = await async_playwright().start()
        launch_options: dict[str, Any] = {
            "headless": headless,
        }

        browser = await playwright.chromium.launch(
            **launch_options, args=["--disable-dev-shm-usage", "--no-sandbox"]
        )

        context = await browser.new_context(
            ignore_https_errors=True, user_agent=ua.random
        )
        await context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            const style = document.createElement('style');
            style.innerHTML = `
                img { display: none !important; }
            `;
            document.head.appendChild(style);
        """
        )
        logger.info("Browser successfully launched.")
        return playwright, browser, context

    except Exception as e:
        logger.error("Error during browser initialization attempt: %s", e)
        raise


class BaseParser(ABC):
    def __init__(self, site: SiteModel):
        self.site = site
        self.date = datetime.today()
        self.currencies: dict[str, float] = {}
        self.total_response_size_kb = 0.0

    def update_response_stats(self, size_kb: float):
        """Update response size statistics for this parser instance."""
        self.total_response_size_kb += size_kb

    @abstractmethod
    async def get_content(
        self,
        date: datetime,
        departure_city: CitySchema,
        arrival_city: CitySchema,
        **kwargs,
    ):
        """Fetches raw data from the website."""
        pass

    @abstractmethod
    def parse_data(
        self,
        content: TicketDataSchema,
        departure_city: CitySchema,
        arrival_city: CitySchema,
    ) -> List[TicketDataSchema]:
        """Parses the fetched data."""
        pass

    def convert_to_pydantic_models(self, trip: TicketDataSchema, route: dict) -> Dict:
        """Converts parsed data into Pydantic models."""
        try:
            route_data = RouteSchema(
                from_city_id=trip.from_city_id,
                to_city_id=trip.to_city_id,
                departure_date=trip.departure_datetime.date(),
                site_id=int(self.site.id),
                parsed_at=datetime.now(),
            )
            trip_data = TripSchema(
                from_station=trip.from_station_name,
                to_station=trip.to_station_name,
                departure_time=trip.departure_datetime.time(),
                arrival_time=(
                    trip.arrival_datetime.time() if trip.arrival_datetime else None
                ),
                arrival_date=(
                    trip.arrival_datetime.date() if trip.arrival_datetime else None
                ),
                carrier_name=trip.carrier_name,
                duration=trip.travel_time,
                is_transfer=bool(trip.is_transfer),
            )

            trip_history_data = TripHistorySchema(
                price=trip.price,
                currency=trip.currency,
                available_seats=trip.available_seats,
            )

            return {
                "route": route_data,
                "trip": trip_data,
                "trip_history": trip_history_data,
            }
        except ValidationError as e:
            logger.error(f"Data validation error: {e}")
            raise e


class BrowserParser(BaseParser, ABC):
    def __init__(self, site: SiteModel):
        super().__init__(site)

    @asynccontextmanager
    async def setup_browser(self, headless: bool = True):
        try:
            playwright, browser, context = await initialize_browser(headless)
            yield browser, context
        except PlaywrightError as e:
            logger.error(f"Playwright error during browser setup: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during browser setup: {e}")
            raise

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(5),
        retry=retry_if_exception_type(ProxyConnectionError),
        after=after_log(logger, log_level=WARNING),  # type: ignore
        reraise=True,
    )
    async def get_content(
        self,
        date: datetime,
        departure_city: CitySchema,
        arrival_city: CitySchema,
        page: Any = None,
        **kwargs,
    ):
        try:
            await allow_only_needed_requests(page)
            await page.goto(self.site.url, timeout=60000)
            logger.info(f"Successfully opened {self.site.url}")

            await self.get_route_html(
                page, date, departure_city, arrival_city, **kwargs
            )

            content = await page.content()
            return content
        except Exception as e:
            if "ERR_CONNECTION_RESET" in str(e):
                logger.warning(f"Connection error: {e}. Retry in 10 sec")
                raise ProxyConnectionError(e)
            logger.error(f"Error while opening site:{self.site.url} | {e}")
            raise e

    @abstractmethod
    async def get_route_html(
        self,
        page,
        date: datetime,
        departure_city: CitySchema,
        arrival_city: CitySchema,
        **kwargs,
    ):
        pass


class RequestParser(BaseParser, ABC):
    def __init__(self, site: SiteModel):
        super().__init__(site)

    @classmethod
    @abstractmethod
    async def create(cls):
        """All subclasses must implement this method"""
        pass

    @classmethod
    async def load_site(cls, site_name: str) -> SiteModel:
        with get_db() as session:
            site = session.query(SiteModel).filter(SiteModel.name == site_name).first()
            if not site or not site.is_active:
                raise ValueError(f"Site '{site_name}' not found or inactive.")
        return site

    async def init_async(self):
        pass

    async def send_request(self, *args, **kwargs):
        """Wrapper around the http_utils.send_request function to track response sizes."""
        response = await send_request(*args, **kwargs)

        size_kb = get_response_size(response)
        self.update_response_stats(size_kb)

        return response

    async def get_content(
        self,
        date: datetime,
        departure_city: CitySchema,
        arrival_city: CitySchema,
        **kwargs,
    ):
        """
        Fetches raw data from the API or website.
        This method should be overridden in subclasses for specific logic.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def parse_data(
        self, response, departure_city: CitySchema, arrival_city: CitySchema
    ) -> List[TicketDataSchema]:
        """
        Parses the response data.
        This method should be overridden in subclasses for specific parsing logic.
        """
        raise NotImplementedError("Subclasses must implement this method.")
