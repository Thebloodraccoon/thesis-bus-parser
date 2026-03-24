from __future__ import annotations

import asyncio
import random
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from thesis.parser.app.repository import (
    db_session,
    SiteRepository,
    RouteRepository,
    TripRepository,
    TripHistoryRepository,
)
from thesis.parser.app.schemas import CitySchema
from thesis.parser.app.scrapers.base import BaseScraper
from thesis.parser.app.services import RouteFetcher
from thesis.parser.app.settings.logger import get_logger

logger = get_logger(__name__)


# Data structures
@dataclass
class ScraperConfig:
    """Runtime configuration for a single pipeline execution."""

    threads: int = 5
    max_duration_seconds: int = 86_400


@dataclass
class RouteData:
    """One scraping task: a city pair for a specific date."""

    departure_city: CitySchema
    arrival_city: CitySchema
    route_id: int
    trip_id: str
    from_date: datetime
    to_date: datetime
    departure_station_id: Optional[int] = None
    arrival_station_id: Optional[int] = None


@dataclass
class _Counters:
    counter: int = 0
    successful_routes: int = 0
    error_routes: int = 0


@dataclass
class PipelineResult:
    """Per-date summary returned by ``ScraperPipeline.run()``."""

    date: str
    successful: int
    errors: int
    total: int


# Metrics helper
class ScraperMetrics:
    """Tracks progress and logs it during the pipeline run."""

    def __init__(self, scraper: BaseScraper) -> None:
        self._scraper = scraper
        self._counts = _Counters()

    def reset(self) -> None:
        self._counts = _Counters()

    def record(self, success: bool) -> None:
        self._counts.counter += 1
        if success:
            self._counts.successful_routes += 1
        else:
            self._counts.error_routes += 1

    def log(self, route: RouteData, total: int) -> None:
        pct = (self._counts.counter / total * 100) if total else 0

        logger.info(
            "%s | %s → %s | %d/%d (%.1f%%) ✓%d ✗%d",
            self._scraper.site.name,
            route.departure_city.name_ua,
            route.arrival_city.name_ua,
            self._counts.counter,
            total,
            pct,
            self._counts.successful_routes,
            self._counts.error_routes,
        )

    @property
    def counts(self) -> _Counters:
        return deepcopy(self._counts)


# Pipeline
class ScraperPipeline:
    """
    Producer/consumer async pipeline.

    * **Producer** – ``run()`` pushes ``RouteData`` tasks into a queue.
    * **Workers**  – ``_worker()`` coroutines pop tasks, call
      ``scraper.fetch() → scraper.parse()`` and enqueue results.
    * **Collector**– ``_collector()`` receives results and updates metrics.
    """

    def __init__(self, scraper: BaseScraper, config: ScraperConfig) -> None:
        self._scraper = scraper
        self._config = config
        self._metrics = ScraperMetrics(scraper)
        self._tasks_q: asyncio.Queue = asyncio.Queue(maxsize=4_000)
        self._results_q: asyncio.Queue = asyncio.Queue()
        self._start: datetime = datetime.now()

    async def run(
        self,
        depth_from: int,
        depth_to: int,
    ) -> List[PipelineResult]:
        self._start = datetime.now()

        dates = [
            self._scraper.date + timedelta(days=i) for i in range(depth_from, depth_to)
        ]
        summary: List[PipelineResult] = []

        try:
            workers = [
                asyncio.create_task(self._worker(i))
                for i in range(self._config.threads)
            ]

            for date in dates:
                result = await self._process_date(date)
                summary.append(result)

            # Signal workers to stop
            for _ in range(self._config.threads):
                await self._tasks_q.put(None)

            await asyncio.gather(*workers)

        except Exception as exc:
            logger.critical("Pipeline failed: %s", exc)
        finally:
            with db_session() as s:
                SiteRepository(s).mark_parsed(self._scraper.site.name)

            logger.info(
                "Pipeline finished in %s",
                datetime.now() - self._start,
            )

        return summary

    async def _process_date(self, date: datetime) -> PipelineResult:
        date_str = date.strftime("%Y-%m-%d")

        logger.info("=== Processing date: %s ===", date_str)
        self._metrics.reset()

        routes = await asyncio.to_thread(RouteFetcher.get_routes, date)
        if not routes:
            logger.warning("No routes for %s, skipping.", date_str)
            return PipelineResult(date_str, 0, 0, 0)

        random.shuffle(routes)
        total = len(routes)
        logger.info("Loaded %d routes for %s", total, date_str)

        collector = asyncio.create_task(self._collector(total))

        for route in routes:
            if self._timeout_exceeded():
                break

            await self._tasks_q.put({"route": route, "date": date})

        await self._tasks_q.join()
        await self._results_q.put(None)
        await collector

        counts = self._metrics.counts
        logger.info(
            "=== Done %s: ✓%d ✗%d ===",
            date_str,
            counts.successful_routes,
            counts.error_routes,
        )

        return PipelineResult(
            date_str,
            counts.successful_routes,
            counts.error_routes,
            total,
        )

    async def _worker(self, worker_id: int) -> None:
        while True:
            task = await self._tasks_q.get()
            if task is None:
                self._tasks_q.task_done()
                break

            try:
                success = await self._run_single(task["route"], task["date"])
            except Exception as exc:
                logger.error("Worker %d fatal: %s", worker_id, exc)
                success = False
            finally:
                self._tasks_q.task_done()

            await self._results_q.put({"success": success, "route": task["route"]})

    async def _collector(self, total: int) -> None:
        while True:
            item = await self._results_q.get()
            if item is None:
                self._results_q.task_done()
                break

            try:
                self._metrics.record(item["success"])
                self._metrics.log(item["route"], total)
            finally:
                self._results_q.task_done()

    async def _run_single(self, route: RouteData, date: datetime) -> bool:
        try:
            content = await self._scraper.fetch(
                date, route.departure_city, route.arrival_city
            )
            if not content:
                return True  # no trips is not an error

            tickets = self._scraper.parse(
                content, route.departure_city, route.arrival_city
            )
            if tickets:
                await asyncio.to_thread(self._persist, tickets)

            return True

        except Exception as exc:
            logger.error(
                "Error on %s → %s: %s",
                route.departure_city.name_ua,
                route.arrival_city.name_ua,
                exc,
            )

            return False

    def _persist(self, tickets) -> None:
        with db_session() as s:
            route_repo = RouteRepository(s)
            trip_repo = TripRepository(s)
            history_repo = TripHistoryRepository(s)

            for ticket in tickets:
                db_dicts = self._scraper.to_db_dicts(ticket)
                route_id = route_repo.get_or_create(db_dicts["route"])
                trip_id = trip_repo.get_or_create(db_dicts["trip"], route_id)
                history_repo.create_if_changed(db_dicts["trip_history"], trip_id)

        logger.debug("Persisted %d tickets.", len(tickets))

    def _timeout_exceeded(self) -> bool:
        elapsed = (datetime.now() - self._start).total_seconds()
        return elapsed >= self._config.max_duration_seconds
