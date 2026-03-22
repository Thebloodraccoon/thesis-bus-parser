import asyncio

from celery import shared_task

from app.parser.managers.task.maintenance_task_manager import MaintenanceTaskManager
from app.parser.managers.task.parser_task_manager import ParserTaskManager


@shared_task(bind=True, acks_late=True, queue="high_priority", name="task_city_update")
def task_city_update(self):
    """Celery task for updating cities."""
    return asyncio.run(MaintenanceTaskManager().run_city_update_task())


@shared_task(bind=True, queue="high_priority", name="task_currency_rate_update")
def task_currency_rate_update(self):
    """Celery task for updating currencies."""
    return asyncio.run(MaintenanceTaskManager().run_currency_update_task())


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
