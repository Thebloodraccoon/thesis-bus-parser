import asyncio

from parser.app.managers.monitoring.service_health import ServiceHealthChecker
from parser.app.managers.monitoring.system_metrics import SystemMetricsCollector
from parser.app.managers.task.base import BaseTaskManager
from parser.app.settings.logger import get_logger

logger = get_logger(__name__)


async def monitor_service_health(
    interval_seconds: int = 60, job_name: str = "service_health"
):
    """Asynchronous function for monitoring the health of services."""

    checker = ServiceHealthChecker(job_name=job_name)
    logger.info(f"Starting service health monitoring with {interval_seconds}s interval")

    try:
        while True:
            try:
                results = await checker.check_all_services()

                if results:
                    summary = results.get("summary", {})
                    logger.info(
                        f"Service health check: "
                        f"{summary.get('healthy_services', 0)}/{summary.get('total_services', 0)} healthy, "
                        f"Duration: {summary.get('check_duration', 0):.3f}s"
                    )
                else:
                    logger.warning("Failed to check service health")

            except Exception as e:
                logger.error(f"Error in service health check: {e}")

            await asyncio.sleep(interval_seconds)

    except asyncio.CancelledError:
        logger.info("Service health monitoring cancelled")
    except Exception as e:
        logger.error(f"Service health monitoring failed: {e}")
    finally:
        logger.info("Service health monitoring stopped")


async def monitor_system_metrics(
    interval_seconds: int = 60, job_name: str = "system_metrics"
):
    """Asynchronous function for monitoring system metrics."""

    collector = SystemMetricsCollector(job_name=job_name)

    logger.info(f"Starting system metrics monitoring with {interval_seconds}s interval")

    try:
        while True:
            try:
                metrics = collector.collect_all_metrics()

                if metrics:
                    logger.info(
                        f"System metrics collected: "
                        f"CPU: {metrics.get('cpu', {}).get('cpu_percent', 'N/A')}%, "
                        f"Memory: {metrics.get('memory', {}).get('memory_percent', 'N/A')}%, "
                        f"Duration: {metrics.get('collection_duration', 0):.3f}s"
                    )
                else:
                    logger.warning("Failed to collect system metrics")

            except Exception as e:
                logger.error(f"Error in system metrics collection: {e}")

            await asyncio.sleep(interval_seconds)

    except asyncio.CancelledError:
        logger.info("System metrics monitoring cancelled")
    except Exception as e:
        logger.error(f"System metrics monitoring failed: {e}")
    finally:
        logger.info("System metrics monitoring stopped")


class MonitoringTaskManager(BaseTaskManager):
    """Universal manager for monitoring tasks (system and service)."""

    def run_continuous_monitoring(
        self, monitoring_type: str, interval: int = 60
    ) -> dict:
        """
        Starts an infinite monitoring loop in a separate event loop.
        monitoring_type: 'system' or 'service'
        """
        job_name = f"{monitoring_type}_monitoring"
        logger.info(f"Starting {job_name} with {interval}s interval")

        if monitoring_type == "service":
            coro = monitor_service_health(interval_seconds=interval, job_name=job_name)
        elif monitoring_type == "system":
            coro = monitor_system_metrics(interval_seconds=interval, job_name=job_name)
        else:
            raise ValueError(f"Unknown monitoring type: {monitoring_type}")

        try:
            self.run_async_loop(coro)
            return {"status": "completed", "type": monitoring_type}
        except Exception as e:
            logger.error(f"{job_name} failed: {e}")
            raise

    @BaseTaskManager.task_wrapper(
        task_name="check_service_health_once", notify_on_success=False
    )
    async def check_service_health_once(self) -> dict:
        checker = ServiceHealthChecker(job_name="service_health_once")
        results = await checker.check_all_services()

        if results:
            self._log_service_summary(results)
            return results
        raise Exception("Service health check returned empty results")

    @BaseTaskManager.task_wrapper(
        task_name="collect_system_metrics_once", notify_on_success=False
    )
    async def collect_system_metrics_once(self) -> dict:
        collector = SystemMetricsCollector(job_name="system_metrics_once")
        metrics = collector.collect_all_metrics()

        if metrics:
            self._log_system_summary(metrics)
            return metrics
        raise Exception("System metrics collection failed")

    @classmethod
    def _log_service_summary(cls, results: dict):
        summary = results.get("summary", {})
        logger.info(
            f"Health Check: {summary.get('healthy_services')}/{summary.get('total_services')} healthy"
        )

    @classmethod
    def _log_system_summary(cls, metrics: dict):
        cpu = metrics.get("cpu", {}).get("cpu_percent", "N/A")
        mem = metrics.get("memory", {}).get("memory_percent", "N/A")
        logger.info(f"System Metrics: CPU {cpu}%, MEM {mem}%")


monitoring_manager = MonitoringTaskManager()
