import json
from typing import List, Optional, Union

from sqlalchemy.orm import Session  # type: ignore

from backend.app.api.celery.schedule.schema import ScheduleCreate, ScheduleUpdate
from backend.app.api.celery.schedule.utils import ScheduleCRUD
from backend.app.api.celery.task.schema import TaskBase, TaskResponse
from backend.app.api.celery.utils import update_celery_cache
from backend.app.api.models import CeleryTasksModel
from backend.app.api.sites.utils import SiteCRUD
from backend.app.exceptions.scraper_exceptions import TaskNotFound, TaskAlreadyExisting


def build_task_args(task_data: TaskBase) -> str:
    return json.dumps(
        [
            task_data.site_name,
            task_data.start_date,
            task_data.end_date,
            task_data.threads,
            task_data.max_duration_seconds,
        ]
    )


def build_schedule_create_or_update(
    task_data: TaskBase,
    is_create: bool = True,
) -> Union[ScheduleUpdate, ScheduleCreate]:
    day_of_week_str = ",".join(map(str, task_data.weekdays)) if task_data.weekdays else "*"

    schedule_kwargs = {
        "minute": task_data.minute,
        "hour": task_data.hour,
        "day_of_month": "*",
        "month_of_year": "*",
        "day_of_week": day_of_week_str,
    }

    if is_create:
        return ScheduleCreate(**schedule_kwargs)

    return ScheduleUpdate(**schedule_kwargs)


def parse_cron_day_of_week(day_of_week: str) -> list[int]:  # noqa: C901
    if not day_of_week or day_of_week == "*":
        return list(range(7))

    result: set[int] = set()

    for part in day_of_week.split(","):
        part = part.strip()

        if part.startswith("*/"):
            try:
                step = int(part[2:])
                if step > 0:
                    result.update(range(0, 7, step))
            except ValueError:
                continue

        elif "-" in part:
            try:
                start, end = map(int, part.split("-"))
                # Clamp to valid range
                start = max(0, min(start, 6))
                end = max(0, min(end, 6))
                result.update(range(start, end + 1))
            except ValueError:
                continue

        else:
            try:
                day = int(part)
                if 0 <= day <= 6:
                    result.add(day)
            except ValueError:
                continue

    return sorted(list(result))


def extract_args(
    task: CeleryTasksModel,
) -> tuple[str | None, int | None, int | None, int | None, int | None]:
    try:
        args = json.loads(task.args)
        return args[0], args[1], args[2], args[3], args[4]
    except Exception as e:
        raise e


class TaskCRUD:
    def __init__(self, db: Session):
        self.db = db
        self.scheduleCRUD = ScheduleCRUD(db)
        self.siteCRUD = SiteCRUD(db)

    def _serialize_task(self, task: CeleryTasksModel) -> Optional[TaskResponse]:
        schedule = self.scheduleCRUD.get_schedule_by_id(task.schedule_id)
        if not schedule:
            return None

        site_name, start_date, end_date, threads, max_duration_seconds = extract_args(
            task
        )
        site_id = None
        if site_name:
            site = self.siteCRUD.get_site_by_name(site_name)
            site_id = int(site.id)  # type: ignore

        return TaskResponse(
            id=task.id,
            name=task.name,
            enabled=task.enabled,
            last_run_at=task.last_run_at,
            total_run_count=task.total_run_count,
            schedule_id=task.schedule_id,
            site_id=site_id,
            start_date=start_date or 0,
            end_date=end_date or 0,
            threads=threads or 5,
            max_duration_seconds=max_duration_seconds or 86400,
            minute=schedule.minute,
            hour=schedule.hour,
            weekdays=parse_cron_day_of_week(schedule.day_of_week),
        )

    def _validate_and_prepare_task_data(self, task_data: TaskBase) -> str:
        self.siteCRUD.get_site_by_name(task_data.site_name)

        task_name = task_data.task_name.strip().replace(" ", "_")
        return task_name

    def _commit_and_refresh(self, task: CeleryTasksModel) -> TaskResponse:
        self.db.commit()
        self.db.refresh(task)

        update_celery_cache(db=self.db)

        return self._serialize_task(task)  # type: ignore

    def get_all_tasks(self) -> List[TaskResponse]:
        tasks = (
            self.db.query(CeleryTasksModel)
            .filter(CeleryTasksModel.queue == "parsing")
            .all()
        )
        return list(filter(None, map(self._serialize_task, tasks)))

    def get_task_by_name(self, name: str) -> Optional[CeleryTasksModel]:
        return (
            self.db.query(CeleryTasksModel)
            .filter(CeleryTasksModel.name == name)
            .first()
        )

    def update_task(self, task_id: int, task_data: TaskBase) -> Optional[TaskResponse]:
        task_to_update = (
            self.db.query(CeleryTasksModel)
            .filter(CeleryTasksModel.id == task_id)
            .first()
        )
        if not task_to_update:
            raise TaskNotFound(task_id)

        task_name = self._validate_and_prepare_task_data(task_data)
        if task_name != task_to_update.name and self.get_task_by_name(task_name):
            raise TaskAlreadyExisting(task_name)

        update_schedule = build_schedule_create_or_update(
            task_data=task_data,
            is_create=False,
        )
        self.scheduleCRUD.update_schedule(
            schedule_data=update_schedule, schedule_id=task_to_update.schedule_id
        )

        task_to_update.name = task_name
        task_to_update.enabled = task_data.enabled
        task_to_update.args = build_task_args(task_data)

        return self._commit_and_refresh(task_to_update)

    def create_task(self, task_data: TaskBase) -> Optional[TaskResponse]:
        self.siteCRUD.get_site_by_name(task_data.site_name)

        task_name = task_data.task_name.strip().replace(" ", "_")
        if self.get_task_by_name(task_name):
            raise TaskAlreadyExisting(task_name)

        schedule_data: ScheduleCreate = build_schedule_create_or_update(
            task_data=task_data
        )
        created_schedule = self.scheduleCRUD.create_schedule(schedule_data)

        created_task = CeleryTasksModel(
            name=task_name,
            task="app.managers.task.run_single_parser",
            enabled=task_data.enabled,
            args=build_task_args(task_data),
            kwargs=json.dumps({}),
            headers=json.dumps({}),
            last_run_at=None,
            total_run_count=0,
            one_off=False,
            queue="parsing",
            discriminator="crontabschedule",
            schedule_id=created_schedule.id,
        )

        self.db.add(created_task)
        return self._commit_and_refresh(created_task)

    def delete_task(self, task_id: int) -> None:
        task_to_delete = (
            self.db.query(CeleryTasksModel)
            .filter(CeleryTasksModel.id == task_id)
            .first()
        )
        if not task_to_delete:
            raise TaskNotFound(task_id)

        self.scheduleCRUD.delete_schedule(task_to_delete.schedule_id)

        self.db.delete(task_to_delete)
        self.db.commit()
