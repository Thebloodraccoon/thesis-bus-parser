from __future__ import annotations

import asyncio
from typing import List

from celery import Celery
from celery.exceptions import SoftTimeLimitExceeded
from kombu import Exchange, Queue
from sqlalchemy_celery_beat.schedulers import DatabaseScheduler  # type: ignore

from thesis.parser.app.orchestrator import ScraperPipeline, ScraperConfig
from thesis.parser.app.scrapers.inbus import InbusScraper
from thesis.parser.app.scrapers.rubikon import RubikonScraper
from thesis.parser.app.scrapers.ukrpas import UkrpasScraper
from thesis.parser.app.scrapers.voyger import VoyagerScraper
from thesis.parser.app.services import (
    RouteFetcher,
    VoyagerCityMatcher,
    InbusCityMatcher,
    UkrpasCityMatcher,
    RubikonCityMatcher,
    CurrencyService,
)
from thesis.parser.app.settings.config import settings
from thesis.parser.app.settings.logger import get_logger

logger = get_logger(__name__)

celery_app = Celery(
    "scraper",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["thesis.parser.app.tasks"],
)

config = {
    "beat_dburi": settings.DATABASE_URL,
    "beat_scheduler": DatabaseScheduler,
    "timezone": "Europe/Kiev",
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "result_expires": 86400,
    "worker_prefetch_multiplier": 1,
    "task_acks_late": True,
    "beat_max_loop_interval": 60,
    "broker_connection_retry_on_startup": True,
    "task_time_limit": 86400,
    "task_soft_time_limit": 82800,
    "broker_transport_options": {"visibility_timeout": 90000},
}

celery_app.conf.task_queues = [
    Queue("parsing", Exchange("parsing"), routing_key="parsing"),
    Queue("high_priority", Exchange("high_priority"), routing_key="high_priority"),
]

celery_app.conf.task_routes = {
    "thesis.parser.app.tasks.run_scraper": {"queue": "parsing"},
    "thesis.parser.app.tasks.update_cities": {"queue": "high_priority"},
    "thesis.parser.app.tasks.update_currencies": {"queue": "high_priority"},
}

celery_app.conf.update(config)

# Registry
_SCRAPERS = {
    "ukrpas": UkrpasScraper,
    "inbus": InbusScraper,
    "rubikon": RubikonScraper,
    "voyager": VoyagerScraper,
}


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Tasks
@celery_app.task(name="scraper.tasks.run_scraper", bind=True)
def run_scraper(
    self,
    site_name: str,
    depth_from: int = 0,
    depth_to: int = 1,
    threads: int = 5,
    max_duration_seconds: int = 86_400,
) -> List[dict]:
    """
    Scrape ticket data for *site_name* over the date range
    [today + depth_from, today + depth_to).
    """

    scraper_cls = _SCRAPERS.get(site_name)
    if not scraper_cls:
        raise ValueError(f"Unknown scraper: '{site_name}'")

    async def _main():
        scraper = await scraper_cls.create()
        pipeline = ScraperPipeline(
            scraper,
            ScraperConfig(threads=threads, max_duration_seconds=max_duration_seconds),
        )

        results = await pipeline.run(depth_from, depth_to)
        return [vars(r) for r in results]

    try:
        return _run(_main())
    except SoftTimeLimitExceeded:
        logger.warning("Scraper '%s' exceeded soft time limit.", site_name)
        raise


@celery_app.task(name="scraper.tasks.update_cities")
def update_cities() -> str:
    """Refresh city directory and resolve site-specific city IDs."""

    async def _main():
        RouteFetcher.sync_cities()
        for matcher_cls in (
            InbusCityMatcher,
            VoyagerCityMatcher,
            UkrpasCityMatcher,
            RubikonCityMatcher,
        ):
            await matcher_cls().run()

    _run(_main())
    return "City update completed."


@celery_app.task(name="scraper.tasks.update_currencies")
def update_currencies() -> str:
    """Fetch current exchange rates from the NBU API."""

    updated = _run(CurrencyService().refresh())
    return f"Updated {len(updated)} currencies."
