from __future__ import annotations

import asyncio
import random
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from thesis.parser.app.repository import (
    db_session,
    SiteRepository,
    RouteRepository,
    TripRepository,
    TripHistoryRepository,
)
from thesis.parser.app.schemas import RouteData
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

    def log(self, route: RouteData, date: datetime, total: int) -> None:
        pct = (self._counts.counter / total * 100) if total else 0

        logger.info(
            f"Processing route: {date.strftime('%Y-%m-%d')} | {self._scraper.site.name} | "
            f"{route.departure_city.name_ua} → {route.arrival_city.name_ua}"
        )

        logger.info(
            f"Progress - Success: {self._counts.successful_routes}, Errors: {self._counts.error_routes}, "
            f"Counter: {self._counts.counter}/{total} ({pct:.1f}%) | {self._scraper.site.name}\n"
        )

    @property
    def counts(self) -> _Counters:
        return deepcopy(self._counts)


# Pipeline
class ScraperPipeline:
    """
    Producer/consumer async pipeline.

    * **Producer** – ``run()`` pushes ``RouteData`` tasks into a queue.
    * **Workers** – ``_worker()`` coroutines pop tasks, call
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

        logger.info(
            f"Initialized ScraperPipeline for '{self._scraper.site.name}' "
            f"(Threads: {self._config.threads}, Timeout: {self._config.max_duration_seconds}s)"
        )

    async def run(
        self,
        depth_from: int,
        depth_to: int,
    ) -> List[PipelineResult]:
        self._start = datetime.now()
        logger.info(
            f"Starting pipeline '{self._scraper.site.name}': "
            f"depth {depth_from} to {depth_to} days ahead."
        )

        dates = [
            self._scraper.date + timedelta(days=i) for i in range(depth_from, depth_to)
        ]
        summary: List[PipelineResult] = []

        try:
            logger.info(f"Spawning {self._config.threads} worker(s)...")
            workers = [
                asyncio.create_task(self._worker(i))
                for i in range(self._config.threads)
            ]

            for date in dates:
                result = await self._process_date(date)
                summary.append(result)

            # Signal workers to stop
            logger.info("Signaling workers to shutdown...")
            for _ in range(self._config.threads):
                await self._tasks_q.put(None)

            await asyncio.gather(*workers)
            logger.info("All workers shut down successfully.")

        except Exception as exc:
            logger.critical(
                f"Pipeline '{self._scraper.site.name}' failed with exception: {exc}"
            )
        finally:
            with db_session() as s:
                SiteRepository(s).mark_parsed(self._scraper.site.name)

            elapsed = datetime.now() - self._start
            logger.info(
                f"Pipeline '{self._scraper.site.name}' finished completely in {elapsed}"
            )

        return summary

    async def _process_date(self, date: datetime) -> PipelineResult:
        date_str = date.strftime("%Y-%m-%d")

        logger.info(f"=== Processing date: {date_str} ===")
        self._metrics.reset()

        routes = await asyncio.to_thread(RouteFetcher.get_routes, date)
        if not routes:
            logger.warning(
                f"No routes received from RouteFetcher for {date_str}, skipping."
            )
            return PipelineResult(date_str, 0, 0, 0)

        random.shuffle(routes)
        total = len(routes)
        logger.info(f"Loaded {total} routes for {date_str}. Adding to queue...")

        collector = asyncio.create_task(self._collector(total))

        for route in routes:
            if self._timeout_exceeded():
                break

            await self._tasks_q.put({"route": route, "date": date})

        logger.info(
            f"Finished queueing {total} routes for {date_str}. Waiting for workers to finish..."
        )
        await self._tasks_q.join()

        await self._results_q.put(None)
        await collector

        counts = self._metrics.counts
        logger.info(
            f"=== Done {date_str}: ✓{counts.successful_routes} successful, ✗{counts.error_routes} errors ==="
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
                logger.info(f"Worker {worker_id} received stop signal. Exiting.")
                break

            try:
                success = await self._run_single(task["route"], task["date"])
            except Exception as exc:
                logger.error(
                    f"Worker {worker_id} encountered fatal error during _run_single: {exc}"
                )
                success = False
            finally:
                self._tasks_q.task_done()

            await self._results_q.put(
                {"success": success, "route": task["route"], "date": task["date"]}
            )

    async def _collector(self, total: int) -> None:
        logger.info("Metrics collector started.")
        while True:
            item = await self._results_q.get()
            if item is None:
                self._results_q.task_done()
                logger.info("Metrics collector shutting down.")
                break

            try:
                self._metrics.record(item["success"])
                self._metrics.log(item["route"], item["date"], total)
            finally:
                self._results_q.task_done()

    async def _run_single(self, route: RouteData, date: datetime) -> bool:
        dep_name = route.departure_city.name_ua
        arr_name = route.arrival_city.name_ua

        try:
            content = await self._scraper.fetch(
                date, route.departure_city, route.arrival_city
            )

            if not content:
                logger.info(f"No trips found for {dep_name} → {arr_name}.")
                return True  # no trips is not an error

            tickets = self._scraper.parse(
                content, route.departure_city, route.arrival_city
            )

            if tickets:
                logger.info(
                    f"Parsed {len(tickets)} tickets for {dep_name} → {arr_name}. Persisting to DB..."
                )
                await asyncio.to_thread(self._persist, tickets)
            else:
                logger.info(
                    f"Scraper returned content for {dep_name} → {arr_name}, but parsed 0 valid tickets."
                )

            return True

        except Exception as exc:
            logger.error(f"Error processing route {dep_name} → {arr_name}: {exc}")
            return False

    def _persist(self, tickets) -> None:
        try:
            with db_session() as s:
                route_repo = RouteRepository(s)
                trip_repo = TripRepository(s)
                history_repo = TripHistoryRepository(s)

                for ticket in tickets:
                    db_dicts = self._scraper.to_db_dicts(ticket)
                    route_id = route_repo.get_or_create(db_dicts["route"])
                    trip_id = trip_repo.get_or_create(db_dicts["trip"], route_id)
                    history_repo.create_if_changed(db_dicts["trip_history"], trip_id)

            logger.info(f"Successfully persisted {len(tickets)} tickets to DB.")
        except Exception as exc:
            logger.error(
                f"Database persistence failed for {len(tickets)} tickets: {exc}"
            )
            raise

    def _timeout_exceeded(self) -> bool:
        elapsed = (datetime.now() - self._start).total_seconds()
        if elapsed >= self._config.max_duration_seconds:
            logger.warning(
                f"Timeout exceeded! Elapsed: {elapsed:.1f}s, "
                f"Max allowed: {self._config.max_duration_seconds}s"
            )
            return True

        return False
