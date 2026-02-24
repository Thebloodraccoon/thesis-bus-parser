from datetime import datetime
from typing import Dict, Optional
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    push_to_gateway,
)

from parser.app.settings.constants import settings
from parser.app.settings.logger import get_logger

logger = get_logger(__name__)


class PushgatewayClient:
    """Client for sending metrics to Pushgateway."""

    def __init__(self, job_name: Optional[str] = None):
        self.job_name = job_name or "scraper"
        self.pushgateway_url = settings.PUSHGATEWAY_URL
        self.registry = CollectorRegistry()

        self._init_metrics()

    def _init_metrics(self):
        """Initializes metrics."""
        # Parsers metrics
        self.parser_requests_total = Counter(
            "parser_requests_total",
            "Total number of parser requests",
            ["parser_name", "site_name"],
            registry=self.registry,
        )

        self.parser_errors_total = Counter(
            "parser_errors_total",
            "Total number of parser errors",
            ["parser_name", "site_name", "error_type"],
            registry=self.registry,
        )

        self.parser_duration_seconds = Histogram(
            "parser_duration_seconds",
            "Parser execution duration in seconds",
            ["parser_name", "site_name"],
            registry=self.registry,
        )

        # Migration metrics
        self.migration_routes_total = Counter(
            "migration_routes_total",
            "Total number of routes migrated",
            ["status"],
            registry=self.registry,
        )

        self.migration_duration_seconds = Histogram(
            "migration_duration_seconds",
            "Migration execution duration in seconds",
            registry=self.registry,
        )

        # Celery metrics
        self.celery_tasks_total = Counter(
            "celery_tasks_total",
            "Total number of Celery tasks",
            ["task_name", "status"],
            registry=self.registry,
        )

        self.celery_task_duration_seconds = Histogram(
            "celery_task_duration_seconds",
            "Celery task execution duration in seconds",
            ["task_name"],
            registry=self.registry,
        )

        # System metric
        self.system_memory_bytes = Gauge(
            "system_memory_bytes",
            "System memory usage in bytes",
            registry=self.registry,
        )

        self.system_cpu_percent = Gauge(
            "system_cpu_percent", "System CPU usage percentage", registry=self.registry
        )

        # Database metrics
        self.database_connections = Gauge(
            "database_connections",
            "Number of active database connections",
            registry=self.registry,
        )

        self.database_size_bytes = Gauge(
            "database_size_bytes", "Database size in bytes", registry=self.registry
        )

        # Gauge Metrics to display current progress in real time
        self.parser_progress_current = Gauge(
            "parser_progress_current",
            "Current number of processed routes",
            ["parser_name", "site_name"],
            registry=self.registry,
        )

        self.parser_progress_total = Gauge(
            "parser_progress_total",
            "Total number of routes to process",
            ["parser_name", "site_name"],
            registry=self.registry,
        )

        self.parser_progress_percentage = Gauge(
            "parser_progress_percentage",
            "Progress percentage (0-100)",
            ["parser_name", "site_name"],
            registry=self.registry,
        )

        # Metrics for calculating Found/not_found in real time
        self.parser_requests_sent = Gauge(
            "parser_requests_sent",
            "Number of requests sent to parser",
            ["parser_name", "site_name"],
            registry=self.registry,
        )

        # Detailed metrics for real -time monitoring
        self.parser_detailed_routes_processed = Gauge(
            "parser_detailed_routes_processed",
            "Current number of processed routes",
            ["parser_name", "site_name", "site_id"],
            registry=self.registry,
        )

        self.parser_detailed_successful_routes = Gauge(
            "parser_detailed_successful_routes",
            "Current number of successful routes",
            ["parser_name", "site_name", "site_id"],
            registry=self.registry,
        )

        self.parser_detailed_error_routes = Gauge(
            "parser_detailed_error_routes",
            "Current number of error routes",
            ["parser_name", "site_name", "site_id"],
            registry=self.registry,
        )

        self.parser_response_size_kb = Gauge(
            "parser_response_size_kb",
            "Current response size in KB",
            ["parser_name", "site_name", "site_id"],
            registry=self.registry,
        )

        self.parser_is_active = Gauge(
            "parser_is_active",
            "Parser activity status (1=active, 0=inactive)",
            ["parser_name", "site_name", "site_id"],
            registry=self.registry,
        )

        self.parser_current_date = Gauge(
            "parser_current_date",
            "Current parsing date (Unix timestamp)",
            ["parser_name", "site_name", "site_id"],
            registry=self.registry,
        )

        # Parser end metrics
        self.parser_completion_total_routes = Counter(
            "parser_completion_total_routes",
            "Total routes processed on completion",
            ["parser_name", "site_name", "site_id"],
            registry=self.registry,
        )

        self.parser_completion_successful_routes = Counter(
            "parser_completion_successful_routes",
            "Total successful routes on completion",
            ["parser_name", "site_name", "site_id"],
            registry=self.registry,
        )

        self.parser_completion_error_routes = Counter(
            "parser_completion_error_routes",
            "Total error routes on completion",
            ["parser_name", "site_name", "site_id"],
            registry=self.registry,
        )

        # General Parser metrics for the entire launch (are not discarded between days)
        self.parser_total_routes_processed = Gauge(
            "parser_total_routes_processed",
            "Total routes processed across all days in current run",
            ["parser_name", "site_name", "site_id"],
            registry=self.registry,
        )

        self.parser_total_successful_routes = Gauge(
            "parser_total_successful_routes",
            "Total successful routes across all days in current run",
            ["parser_name", "site_name", "site_id"],
            registry=self.registry,
        )

        self.parser_total_error_routes = Gauge(
            "parser_total_error_routes",
            "Total error routes across all days in current run",
            ["parser_name", "site_name", "site_id"],
            registry=self.registry,
        )

    def push_metrics(self, grouping_key: Optional[Dict[str, str]] = None):
        """Sends metrics to Pushgateway."""

        grouping_key = grouping_key or {"instance": "scraper"}

        push_to_gateway(
            self.pushgateway_url,
            job=self.job_name,
            grouping_key=grouping_key,
            registry=self.registry,
        )

        logger.debug(f"Metrics pushed to Pushgateway: {self.pushgateway_url}")

    def record_parser_metrics(
        self,
        parser_name: str,
        site_name: str,
        routes_processed: int,
        errors: int,
        duration: float,
        error_type: str = "unknown",
    ):
        """Records Parser's metrics."""

        try:
            self.parser_requests_total.labels(
                parser_name=parser_name, site_name=site_name
            ).inc(routes_processed)

            if errors > 0:
                self.parser_errors_total.labels(
                    parser_name=parser_name, site_name=site_name, error_type=error_type
                ).inc(errors)

            self.parser_duration_seconds.labels(
                parser_name=parser_name, site_name=site_name
            ).observe(duration)

            logger.info(
                f"Parser metrics recorded - {parser_name} ({site_name}): "
                f"routes={routes_processed}, errors={errors}, duration={duration:.2f}s"
            )

        except Exception as e:
            logger.error(f"❌ Failed to record parser metrics: {e}")

    def record_migration_metrics(
        self, routes_migrated: int, errors: int, duration: float
    ):
        """Records migration metrics."""
        try:
            self.migration_routes_total.labels(status="success").inc(routes_migrated)
            if errors > 0:
                self.migration_routes_total.labels(status="error").inc(errors)

            self.migration_duration_seconds.observe(duration)

            logger.info(
                f"Migration metrics recorded: routes={routes_migrated}, "
                f"errors={errors}, duration={duration:.2f}s"
            )

        except Exception as e:
            logger.error(f"❌ Failed to record migration metrics: {e}")

    def record_celery_metrics(
        self, task_name: str, status: str, duration: float = None
    ):
        """Records the metrics of the Celery task."""
        try:
            self.celery_tasks_total.labels(task_name=task_name, status=status).inc()

            if duration is not None:
                self.celery_task_duration_seconds.labels(task_name=task_name).observe(
                    duration
                )

            logger.info(
                f"Celery metrics recorded - {task_name}: status={status}, "
                f"duration={duration:.2f}s"
                if duration
                else "duration=unknown"
            )

        except Exception as e:
            logger.error(f"❌ Failed to record Celery metrics: {e}")

    def update_parser_progress(
        self,
        parser_name: str,
        site_name: str,
        current_processed: int,
        total_routes: int,
    ):
        """Updates the scraper's progress in real-time."""
        try:
            self.parser_progress_current.labels(
                parser_name=parser_name, site_name=site_name
            ).set(current_processed)

            self.parser_progress_total.labels(
                parser_name=parser_name, site_name=site_name
            ).set(total_routes)

            if total_routes > 0:
                percentage = (current_processed / total_routes) * 100
                self.parser_progress_percentage.labels(
                    parser_name=parser_name, site_name=site_name
                ).set(percentage)

            self.parser_requests_sent.labels(
                parser_name=parser_name, site_name=site_name
            ).set(current_processed)

        except Exception as e:
            logger.error(f"❌ Failed to update parser progress: {e}")

    def record_detailed_parser_metrics(
        self,
        parser_name: str,
        site_name: str,
        site_id: int,
        routes_processed: int,
        total_routes: int,
        successful_routes: int,
        error_routes: int,
        response_size_kb: float,
        current_date=None,
        is_active: bool = True,
    ):
        """Records detailed parser metrics in real time."""
        try:
            site_id_str = str(site_id)

            self.parser_detailed_routes_processed.labels(
                parser_name=parser_name, site_name=site_name, site_id=site_id_str
            ).set(routes_processed)

            self.parser_detailed_successful_routes.labels(
                parser_name=parser_name, site_name=site_name, site_id=site_id_str
            ).set(successful_routes)

            self.parser_detailed_error_routes.labels(
                parser_name=parser_name, site_name=site_name, site_id=site_id_str
            ).set(error_routes)

            self.parser_response_size_kb.labels(
                parser_name=parser_name, site_name=site_name, site_id=site_id_str
            ).set(response_size_kb)

            self.parser_is_active.labels(
                parser_name=parser_name, site_name=site_name, site_id=site_id_str
            ).set(1 if is_active else 0)

            if current_date:
                try:
                    if isinstance(current_date, str):
                        date_obj = datetime.strptime(current_date, "%Y-%m-%d")
                    else:
                        date_obj = datetime.combine(current_date, datetime.min.time())

                    timestamp = int(date_obj.timestamp())

                    self.parser_current_date.labels(
                        parser_name=parser_name,
                        site_name=site_name,
                        site_id=site_id_str,
                    ).set(timestamp)

                except Exception as e:
                    logger.warning(f"Failed to set current date metric: {e}")

            self.update_parser_progress(
                parser_name=parser_name,
                site_name=site_name,
                current_processed=routes_processed,
                total_routes=total_routes,
            )

            if not hasattr(self, "_previous_values"):
                self._previous_values = {}

            key = f"{parser_name}_{site_name}_{site_id_str}"
            prev_values = self._previous_values.get(
                key, {"routes_processed": 0, "successful_routes": 0, "error_routes": 0}
            )

            routes_diff = routes_processed - prev_values["routes_processed"]
            successful_diff = successful_routes - prev_values["successful_routes"]
            error_diff = error_routes - prev_values["error_routes"]

            if routes_diff > 0:
                self.parser_total_routes_processed.labels(
                    parser_name=parser_name, site_name=site_name, site_id=site_id_str
                ).inc(routes_diff)

            if successful_diff > 0:
                self.parser_total_successful_routes.labels(
                    parser_name=parser_name, site_name=site_name, site_id=site_id_str
                ).inc(successful_diff)

            if error_diff > 0:
                self.parser_total_error_routes.labels(
                    parser_name=parser_name, site_name=site_name, site_id=site_id_str
                ).inc(error_diff)

            self._previous_values[key] = {
                "routes_processed": routes_processed,
                "successful_routes": successful_routes,
                "error_routes": error_routes,
            }

            logger.debug(
                f"Detailed parser metrics recorded for {parser_name}: "
                f"processed={routes_processed}/{total_routes}, "
                f"success={successful_routes}, errors={error_routes}, "
                f"response_size={response_size_kb:.2f}KB, active={is_active}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to record detailed parser metrics: {e}")

    def deactivate_parser(self, parser_name: str, site_name: str, site_id: int):
        """Deactivates the Parser (sets IS_active = 0)."""

        try:
            site_id_str = str(site_id)

            self.parser_is_active.labels(
                parser_name=parser_name, site_name=site_name, site_id=site_id_str
            ).set(0)

            logger.info(f"Parser {parser_name} deactivated")

        except Exception as e:
            logger.error(f"❌ Failed to deactivate parser {parser_name}: {e}")
