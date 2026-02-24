import asyncio
import functools
import time
from datetime import datetime
from typing import Any, Dict, Callable

from parser.app.managers.monitoring.metrics import MetricsCollector
from parser.app.settings.logger import get_logger

logger = get_logger(__name__)


class BaseTaskManager:
    """
    Basic task manager.
    Provides shared resources and a decorator to handle task execution.
    """

    def __init__(self):
        self.metrics = MetricsCollector()

    @staticmethod
    def task_wrapper(task_name: str, notify_on_success: bool = True):
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(self, *args, **kwargs) -> Dict[str, Any]:
                start_time = datetime.now()
                start_ts = time.time()
                task_id = f"{task_name}_{start_time.strftime('%Y%m%d_%H%M%S')}"

                logger.info(f"Task Started: {task_id} | Name: {task_name}")

                try:
                    result_data = await func(self, *args, **kwargs)

                    duration = time.time() - start_ts

                    self.metrics.record_celery_metrics(
                        task_name=task_name, status="success", duration=duration
                    )

                    success_msg = f"Task {task_name} completed in {duration:.2f}s"
                    logger.info(f"{success_msg}. Result: {str(result_data)[:100]}...")

                    return {
                        "task_id": task_id,
                        "status": "success",
                        "result": result_data,
                        "duration": duration,
                        "completed_at": datetime.now().isoformat(),
                    }

                except Exception as e:
                    duration = time.time() - start_ts
                    error_msg = str(e)

                    logger.exception(f"Task {task_id} failed: {error_msg}")

                    self.metrics.record_celery_metrics(
                        task_name=task_name, status="error", duration=duration
                    )

                    await self.notifier.send_error(
                        f"Task {task_name} failed: {error_msg}"
                    )

                    return {
                        "task_id": task_id,
                        "status": "error",
                        "error": error_msg,
                        "duration": duration,
                        "completed_at": datetime.now().isoformat(),
                    }

            return wrapper

        return decorator

    @classmethod
    def run_async_loop(cls, coro):
        """Helper to start a coroutine in a new event loop (for synchronous entry points)."""

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
