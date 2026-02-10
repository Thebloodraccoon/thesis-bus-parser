from datetime import datetime

from app.scraper.schemas.types import ParsingCounters, RouteData
from app.settings.logger import get_logger

logger = get_logger(__name__)


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