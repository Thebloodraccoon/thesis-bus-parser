import asyncio
import random
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timedelta

from parser.app.db.site_db import write_last_parsed
from parser.app.managers.browser.browser_manager import BrowserManager
from parser.app.managers.http.route_fetcher import RouteFetcher
from parser.app.managers.monitoring.parser_metrics_service import ParserMetricsService
from parser.app.managers.parser.parser_route_manager import RouteProcessingManager
from parser.app.parsers.base_parser import BrowserParser
from parser.app.schemas.types import ParsingConfig, ParsingResult
from parser.app.settings.logger import get_logger

logger = get_logger(__name__)

class ParserManager:
    def __init__(self, parser_class, config: ParsingConfig):
        self.parser_class = parser_class
        self.config = config

        # Browser Manager
        self.browser_manager = None
        if isinstance(parser_class, BrowserParser):
            self.browser_manager = BrowserManager(
                parser_class, use_proxy=config.use_proxy
            )

        # Logic Processor
        self.route_processor = RouteProcessingManager(parser_class, config)

        # Metrics & State Service
        self.metrics_service = ParserMetricsService(parser_class)

        # Queues
        self.tasks_queue = asyncio.Queue(maxsize=4000)
        self.results_queue = asyncio.Queue()

        self.start_time = datetime.now()
        self.dates = None

    async def worker(self, worker_id: int):
        """Consumer: Executes the task and returns the result."""
        while True:
            task = await self.tasks_queue.get()

            if task is None:
                self.tasks_queue.task_done()
                break

            try:
                result_data = await self.route_processor.process_single_route(
                    route=task["route"],
                    selected_date=task["date"],
                    browser_manager=self.browser_manager,
                    max_duration_seconds=task["max_duration_seconds"],
                    start_time=task["pipeline_start_time"],
                )

                if not result_data:
                    result_data = {
                        "result": ParsingResult(success=False),
                        "stats": {"error": 1},
                        "date": task["date"],
                    }

                result_data["route_object"] = task["route"]

                await self.results_queue.put(result_data)

            except Exception as e:
                logger.error(f"Worker {worker_id} critical error: {e}")
                await self.results_queue.put(
                    {
                        "result": ParsingResult(success=False, error=str(e)),
                        "stats": {"error": 1},
                        "date": task["date"],
                        "route_object": task["route"],
                    }
                )
            finally:
                self.tasks_queue.task_done()

    async def result_collector(self, total_routes_count: int, current_date: datetime):
        logger.info("Collector started...")

        while True:
            data = await self.results_queue.get()

            if data is None:
                self.results_queue.task_done()
                break

            try:
                stats = data.get("stats", {})
                route = data.get("route_object")
                date_obj = data.get("date")

                self.metrics_service.update_buffer(stats)

                if route and date_obj:
                    self.metrics_service.log_progress(
                        route, date_obj, total_routes_count
                    )

                current_count = self.metrics_service.stats_buffer.counter
                if current_count > 0 and current_count % 10 == 0:
                    logger.info(
                        f"Batch flush: Saving metrics at {current_count}/{total_routes_count}..."
                    )
                    self.metrics_service.flush_to_db_and_prometheus(
                        current_date=current_date,
                        total_routes_count=total_routes_count,
                        is_final=False,
                    )

            except Exception as e:
                logger.error(f"Collector logic error: {e}")
            finally:
                self.results_queue.task_done()

    async def run_parser(
        self, depth_from: int, depth_to: int, max_duration_seconds: int = None
    ):
        """Main Entrypoint."""
        self.start_time = datetime.now()

        self.dates = [
            self.parser_class.date + timedelta(days=i)
            for i in range(depth_from, depth_to)
        ]
        date_counters_summary = {}

        self.metrics_service.init_metrics()

        browser_context = None
        try:
            if self.browser_manager:
                browser_context = self.browser_manager.get_browser(headless=True)
                await browser_context.__aenter__()

            workers = [
                asyncio.create_task(self.worker(i)) for i in range(self.config.threads)
            ]

            for date in self.dates:
                date_str = date.strftime("%Y-%m-%d")
                logger.info(f"=== Starting processing for date: {date_str} ===")

                self.metrics_service.reset()

                routes = await asyncio.to_thread(
                    RouteFetcher().get_routes, date
                )

                if not routes:
                    logger.warning(f"No routes found for {date_str}, skipping.")
                    continue

                random.shuffle(routes)

                total_routes_for_day = len(routes)
                logger.info(f"Loaded {total_routes_for_day} tasks for {date_str}")

                collector_task = asyncio.create_task(
                    self.result_collector(total_routes_for_day, date)
                )

                for route in routes:
                    task = {
                        "route": route,
                        "date": date,
                        "max_duration_seconds": max_duration_seconds,
                        "pipeline_start_time": self.start_time,
                        "total_routes_count": total_routes_for_day,
                    }
                    await self.tasks_queue.put(task)

                await self.tasks_queue.join()

                await self.results_queue.put(None)
                await collector_task

                logger.success(f"=== Finished processing for date: {date_str} ===")
                date_counters_summary[date_str] = asdict(
                    deepcopy(self.metrics_service.stats_buffer)
                )

                self.metrics_service.flush_to_db_and_prometheus(
                    current_date=date,
                    total_routes_count=total_routes_for_day,
                    is_final=True,
                )

            for _ in range(self.config.threads):
                await self.tasks_queue.put(None)
            await asyncio.gather(*workers)

            return date_counters_summary

        except Exception as e:
            logger.critical(f"Pipeline failed: {e}")

        finally:
            if self.browser_manager and browser_context:
                await browser_context.__aexit__(None, None, None)

            await asyncio.to_thread(write_last_parsed, self.parser_class.site.name)
            logger.success(
                f"Parser pipeline finished in {datetime.now() - self.start_time}"
            )
