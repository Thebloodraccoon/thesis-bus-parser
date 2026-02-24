from celery import Celery  # type: ignore
from celery.schedules import crontab  # type: ignore
from kombu import Exchange, Queue  # type: ignore
from sqlalchemy_celery_beat.schedulers import DatabaseScheduler  # type: ignore

from parser.app.settings.constants import settings

celery_app = Celery(
    "parser.app.managers.task",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["parser.app.managers.task"],
)

config = {
    "beat_dburi": settings.DATABASE_URL,
    "beat_scheduler": DatabaseScheduler,
    "timezone": "Europe/Kiev",
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "result_expires": 86400,
    "worker_prefetch_multiplier": 1,
    "task_acks_late": True,
    "beat_max_loop_interval": 60,
    "broker_connection_retry_on_startup": True,
    "task_time_limit": 86400,
    "task_soft_time_limit": 82800,
    "broker_transport_options": {"visibility_timeout": 90000},
}


celery_app.conf.task_queues = [
    Queue("parsing", Exchange("parsing"), routing_key="parsing"),
    Queue("high_priority", Exchange("high_priority"), routing_key="high_priority"),
]

celery_app.conf.task_routes = {
    "run_single_parser": {"queue": "parsing"},
    "task_city_update": {"queue": "high_priority"},
    "task_db_migration": {"queue": "high_priority"},
    "task_currency_rate_update": {"queue": "high_priority"},
    "task_delete_inactive_parser_stats": {"queue": "high_priority"},
    "collect_system_metrics_once": {"queue": "high_priority"},
    "system_monitoring": {"queue": "high_priority"},
    "check_service_health_once": {"queue": "high_priority"},
    "service_health_monitoring": {"queue": "high_priority"},
}

celery_app.conf.update(config)