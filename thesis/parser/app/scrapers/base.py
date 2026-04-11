from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from logging import WARNING
from typing import Any, Dict, List, Optional, AsyncGenerator

import httpx
from playwright.async_api import async_playwright
from pydantic import ValidationError
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random,
)

from thesis.core.models import SiteModel
from thesis.parser.app.repository import db_session, CurrencyRepository, SiteRepository
from thesis.parser.app.schemas import (
    TicketData,
    CitySchema,
    TripHistorySchema,
    TripSchema,
    RouteSchema,
)
from thesis.parser.app.settings.config import settings
from thesis.parser.app.settings.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def get_async_client(
    timeout: int = 30, cookies: Optional[dict] = None, **kwargs: Any
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Universal context manager for httpx. AsyncClient with proxy support."""

    client_kwargs = {
        "timeout": timeout,
        "cookies": cookies,
        "follow_redirects": True,
        **kwargs,
    }
    if settings.PROXY_URL:
        client_kwargs["proxy"] = settings.PROXY_URL

    async with httpx.AsyncClient(**client_kwargs) as client:
        yield client


@retry(
    stop=stop_after_attempt(10),
    wait=wait_random(min=0.2, max=2),
    retry=retry_if_exception_type(
        (
            httpx.RequestError,
            httpx.HTTPStatusError,
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.ReadTimeout,
        )
    ),
    after=after_log(logger, log_level=WARNING),
    reraise=True,
)
async def _http_get(
    url: str,
    *,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
    cookies: Optional[dict] = None,
    timeout: int = 30,
) -> httpx.Response:
    async with get_async_client(timeout=timeout, cookies=cookies) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()

        return resp


@retry(
    stop=stop_after_attempt(10),
    wait=wait_random(min=0.2, max=2),
    retry=retry_if_exception_type(
        (
            httpx.RequestError,
            httpx.HTTPStatusError,
            httpx.TimeoutException,
        )
    ),
    after=after_log(logger, log_level=WARNING),
    reraise=True,
)
async def _http_post(
    url: str,
    *,
    params: Optional[dict] = None,
    json: Optional[dict] = None,
    data: Optional[dict] = None,
    headers: Optional[dict] = None,
    timeout: int = 30,
) -> httpx.Response:
    async with get_async_client(timeout=timeout) as client:
        resp = await client.post(
            url, params=params, json=json, data=data, headers=headers
        )
        resp.raise_for_status()
        return resp


def _to_uah(ticket: TicketData, currencies: Dict[str, float]) -> TicketData:
    """Convert ticket price to UAH using the cached rate table."""

    if ticket.currency == "UAH":
        return ticket
    rate = currencies.get(ticket.currency)
    if rate is None:
        with db_session() as s:
            obj = CurrencyRepository(s).get_by_code(ticket.currency)
            if obj:
                rate = float(obj.rate)
                currencies[ticket.currency] = rate
    if rate is None:
        raise ValueError(f"No exchange rate for currency '{ticket.currency}'.")
    ticket.price = (ticket.price * Decimal(str(rate))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    ticket.currency = "UAH"
    return ticket


class BaseScraper(ABC):
    """
    Abstract base for all scrapers.

    Attributes
    ----------
    site : SiteModel
        ORM row for the target website loaded from the DB.
    date : datetime
        The day this scraper instance is associated with.
    currencies : dict
        Local cache of exchange rates (code → float).
    """

    def __init__(self, site: SiteModel) -> None:
        self.site: SiteModel = site
        self.date: datetime = datetime.today()
        self.currencies: Dict[str, float] = {}

    @classmethod
    @abstractmethod
    async def create(cls) -> "BaseScraper":
        """Async factory: load site config, initialize connections."""

    @abstractmethod
    async def fetch(
        self,
        date: datetime,
        departure_city: CitySchema,
        arrival_city: CitySchema,
        **kwargs: Any,
    ) -> Any:
        """Retrieve raw content for the given route and date."""

    @abstractmethod
    def parse(
        self,
        content: Any,
        departure_city: CitySchema,
        arrival_city: CitySchema,
    ) -> List[TicketData]:
        """Convert raw content to a list of ``TicketData`` objects."""

    @classmethod
    async def _load_site(cls, name: str) -> SiteModel:
        with db_session() as s:
            site = SiteRepository(s).get_by_name(name)
            if not site or not site.is_active:
                raise ValueError(f"Site '{name}' not found or inactive.")
        return site

    def to_db_dicts(
        self, ticket: TicketData
    ) -> Dict[str, RouteSchema | TripSchema | TripHistorySchema]:
        """Convert a ``TicketData`` to the three DB schemas needed by the repo."""
        try:
            return {
                "route": RouteSchema(
                    from_city_id=ticket.from_city_id,
                    to_city_id=ticket.to_city_id,
                    departure_date=ticket.departure_datetime.date(),
                    site_id=int(self.site.id),
                    parsed_at=datetime.now(),
                ),
                "trip": TripSchema(
                    from_station=ticket.from_station_name,
                    to_station=ticket.to_station_name,
                    departure_time=ticket.departure_datetime.time(),
                    arrival_time=ticket.arrival_datetime.time()
                    if ticket.arrival_datetime
                    else None,
                    arrival_date=ticket.arrival_datetime.date()
                    if ticket.arrival_datetime
                    else None,
                    carrier_name=ticket.carrier_name,
                    duration=ticket.travel_time,
                    is_transfer=bool(ticket.is_transfer),
                ),
                "trip_history": TripHistorySchema(
                    price=ticket.price,
                    currency=ticket.currency,
                    available_seats=ticket.available_seats,
                ),
            }
        except ValidationError as exc:
            logger.error("Validation error converting ticket: %s", exc)
            raise


class RequestScraper(BaseScraper, ABC):
    """Superclass for all scrapers that communicate via plain HTTP."""

    async def _get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await _http_get(url, **kwargs)

    async def _post(self, url: str, **kwargs: Any) -> httpx.Response:
        return await _http_post(url, **kwargs)


class BrowserScraper(BaseScraper, ABC):
    """
    Superclass for scrapers that require a real browser (Playwright).
    Provides ``setup_browser()`` context manager.
    """

    @asynccontextmanager
    async def setup_browser(self, *, headless: bool = True):
        playwright = await async_playwright().start()
        try:
            launch_kwargs = {
                "headless": headless,
                "args": ["--disable-dev-shm-usage", "--no-sandbox"],
            }

            if settings.PROXY_URL:
                launch_kwargs["proxy"] = {"server": settings.PROXY_URL}

            browser = await playwright.chromium.launch(**launch_kwargs)
            context = await browser.new_context(ignore_https_errors=True)
            await context.add_init_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
            )
            try:
                yield browser, context
            finally:
                await context.close()
                await browser.close()
        finally:
            await playwright.stop()
