import asyncio

from celery import shared_task

from app.scraper.managers.task.maintenance_task_manager import MaintenanceTaskManager
from app.scraper.managers import MonitoringTaskManager
from app.scraper.managers.task.parser_task_manager import ParserTaskManager


@shared_task(bind=True, acks_late=True, queue="high_priority", name="task_city_update")
def task_city_update(self):
    """Celery task for updating cities."""
    return asyncio.run(MaintenanceTaskManager().run_city_update_task())


@shared_task(bind=True, queue="high_priority", name="task_db_migration")
def task_db_migration(self):
    """Celery task for migration of the database."""
    return asyncio.run(MaintenanceTaskManager().run_db_migration_task())


@shared_task(bind=True, queue="high_priority", name="task_currency_rate_update")
def task_currency_rate_update(self):
    """Celery task for updating currencies."""
    return asyncio.run(MaintenanceTaskManager().run_currency_update_task())


@shared_task(bind=True, queue="high_priority", name="task_delete_inactive_parser_stats")
def task_delete_inactive_parser_stats(self):
    """Celery task for cleaning statistics."""
    return asyncio.run(MaintenanceTaskManager().run_cleanup_task())


@shared_task(bind=True, name="service_health_monitoring")
def run_service_health_monitoring(self, interval_seconds: int = 60):
    """Celery task to launch the health monitoring of services."""
    return MonitoringTaskManager().run_continuous_monitoring(
        "service", interval_seconds
    )


@shared_task(bind=True, name="check_service_health_once")
def check_service_health_once(self):
    """Celery task for a single check of the health of services."""
    return asyncio.run(MonitoringTaskManager().check_service_health_once())


@shared_task(bind=True, name="system_monitoring")
def run_system_monitoring(self, interval_seconds: int = 60):
    """Celery task for launching systemic monitoring."""
    return MonitoringTaskManager().run_continuous_monitoring("system", interval_seconds)


@shared_task(bind=True, name="collect_system_metrics_once")
def collect_system_metrics_once(self):
    """Celery task for a single collection of system metrics."""
    return asyncio.run(MonitoringTaskManager().collect_system_metrics_once())


@shared_task(bind=True, queue="parsing", acks_late=True)
def run_single_parser(
    self,
    site_name: str,
    depth_from: int = 0,
    depth_to: int = 0,
    threads: int = 5,
    max_duration_seconds: int = 86400,
    use_proxy: bool = True,
):
    """Celery task for launching a parser."""
    return asyncio.run(
        ParserTaskManager().run_parser(
            site_name, depth_from, depth_to, threads, max_duration_seconds, use_proxy
        )
    )
