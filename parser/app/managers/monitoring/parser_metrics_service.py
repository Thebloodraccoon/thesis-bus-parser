from datetime import datetime
from typing import Dict, Any

from parser.app.db.db_helper import logger
from parser.app.managers.monitoring.pushgateway_client import PushgatewayClient
from parser.app.schemas.types import ParsingCounters, RouteData


def push_parser_metrics(
    site_id: int,
    site_name: str,
    total_count: int,
    counter: Dict[str, Any],
    parser_instance=None,
    current_date=None,
    is_final: bool = False,
    client=None,
):
    """Sends Parser's metrics in Prometheus."""

    try:
        response_size_kb = (
            getattr(parser_instance, "total_response_size_kb", 0.0)
            if parser_instance
            else 0.0
        )
        if client is None:
            client = PushgatewayClient(job_name=f"scraper_{site_name}")

        client.record_detailed_parser_metrics(
            parser_name=site_name,
            site_name=site_name,
            site_id=site_id,
            routes_processed=counter["counter"],
            total_routes=total_count,
            successful_routes=counter["successful_routes"],
            error_routes=counter["error_routes"],
            response_size_kb=response_size_kb,
            current_date=current_date,
            is_active=not is_final,
        )

        client.push_metrics()

        logger.debug(
            f"Prometheus metrics pushed for {site_name}: "
            f"processed={counter['counter']}/{total_count}, "
            f"success={counter['successful_routes']}, "
            f"errors={counter['error_routes']}, "
            f"response_size={response_size_kb:.2f}KB"
        )

    except Exception as e:
        logger.error(f"Failed to push Prometheus metrics for {site_name}: {e}")


class ParserMetricsService:
    def __init__(self, parser_class):
        self.parser_class = parser_class
        self.stats_buffer = ParsingCounters()

    def reset(self):
        """Reset counters before the start of a new day."""
        self.stats_buffer = ParsingCounters()

    def _get_stats_dict(self):
        if hasattr(self.stats_buffer, "dict"):
            return self.stats_buffer.dict()
        elif hasattr(self.stats_buffer, "model_dump"):
            return self.stats_buffer.model_dump()
        else:
            return self.stats_buffer.__dict__

    def init_metrics(self):
        try:
            stats_dict = self._get_stats_dict()

            push_parser_metrics(
                site_id=self.parser_class.site.id,
                site_name=self.parser_class.site.name,
                total_count=0,
                counter=stats_dict,
                parser_instance=self.parser_class,
                current_date=datetime.now(),
                is_final=False,
            )

            logger.info(f"Metrics initialized for {self.parser_class.site.name}")
        except Exception as e:
            logger.error(f"Failed to initialize metrics: {e}")

    def update_buffer(self, result_stats: dict):
        self.stats_buffer.successful_routes += result_stats.get("success", 0)
        self.stats_buffer.error_routes += result_stats.get("error", 0)
        self.stats_buffer.counter += 1

    def log_progress(self, route: RouteData, date: datetime, total_routes: int):
        logger.info(
            f"Processing route: {date.strftime('%Y-%m-%d')} | {self.parser_class.site.name} | "
            f"{route.departure_city.name_ua} -> {route.arrival_city.name_ua}"
        )

        progress_percent = (
            (self.stats_buffer.counter / total_routes * 100) if total_routes > 0 else 0
        )
        logger.info(
            f"Progress - Success: {self.stats_buffer.successful_routes}, Errors: {self.stats_buffer.error_routes}, "
            f"Counter: {self.stats_buffer.counter}/{total_routes} ({progress_percent:.1f}%) | {self.parser_class.site.name}"
        )

    def flush_to_db_and_prometheus(
        self,
        current_date,
        total_routes_count: int,
        is_final=False,
    ):
        try:
            stats_dict = (
                self.stats_buffer.dict()
                if hasattr(self.stats_buffer, "dict")
                else self.stats_buffer.__dict__
            )

            push_parser_metrics(
                site_id=self.parser_class.site.id,
                site_name=self.parser_class.site.name,
                total_count=total_routes_count,
                counter=stats_dict,
                parser_instance=self.parser_class,
                current_date=current_date,
                is_final=is_final,
            )

        except Exception as e:
            logger.error(f"Error flushing metrics: {e}")
