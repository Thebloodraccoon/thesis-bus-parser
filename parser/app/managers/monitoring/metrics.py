from parser.app.managers.monitoring.pushgateway_client import PushgatewayClient
from parser.app.settings.logger import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """Basic collector metric."""

    def __init__(self):
        self.pushgateway_client = PushgatewayClient()

    def record_parser_metrics(
        self,
        parser_name: str,
        site_name: str,
        routes_processed: int,
        errors: int,
        duration: float,
        timeout: bool = False,
        error_type: str = "unknown",
    ):
        """Records Parser's metrics."""

        try:
            self.pushgateway_client.record_parser_metrics(
                parser_name=parser_name,
                site_name=site_name,
                routes_processed=routes_processed,
                errors=errors,
                duration=duration,
                error_type=error_type,
            )

            self.pushgateway_client.push_metrics()
            logger.info(
                f"Parser metrics - {parser_name} ({site_name}): "
                f"routes={routes_processed}, errors={errors}, "
                f"duration={duration:.2f}s, timeout={timeout}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to record parser metrics: {e}")

    def record_celery_metrics(
        self, task_name: str, status: str, duration: float = None
    ):
        """Records metrics of Ceelery tasks."""

        try:
            self.pushgateway_client.record_celery_metrics(
                task_name=task_name, status=status, duration=duration
            )

            self.pushgateway_client.push_metrics()

            logger.info(
                f"Celery metrics - {task_name}: status={status}, "
                f"duration={duration:.2f}s"
                if duration
                else "duration=unknown"
            )

        except Exception as e:
            logger.error(f"❌ Failed to record Celery metrics: {e}")

    def record_migration_metrics(
        self, routes_migrated: int, errors: int, duration: float
    ):
        """Records metric migration."""

        try:
            self.pushgateway_client.record_migration_metrics(
                routes_migrated=routes_migrated, errors=errors, duration=duration
            )

            self.pushgateway_client.push_metrics()
            logger.info(
                f"Migration metrics: routes={routes_migrated}, "
                f"errors={errors}, duration={duration:.2f}s"
            )

        except Exception as e:
            logger.error(f"❌ Failed to record migration metrics: {e}")
