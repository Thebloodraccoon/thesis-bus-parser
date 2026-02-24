from typing import List

from fastapi import APIRouter, Depends, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from backend.app.api.auth.utils import get_current_user, admin_only
from backend.app.api.celery.task.schema import TaskResponse, TaskBase
from backend.app.api.celery.task.utils import TaskCRUD
from backend.app.models.users import User
from backend.app.settings import settings

router = APIRouter(prefix="/celery/task", tags=["Celery Tasks"])


@router.get("/", response_model=List[TaskResponse])
def get_all_tasks(
    db: Session = Depends(settings.get_scraper_db),
    _: User = Depends(get_current_user),
):
    task = TaskCRUD(db).get_all_tasks()
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def get_update_task(
    task_id: int,
    task_data: TaskBase,
    db: Session = Depends(settings.get_scraper_db),
    _: User = Depends(admin_only),
):
    task = TaskCRUD(db).update_task(task_id=task_id, task_data=task_data)
    return task


@router.post("/", response_model=TaskResponse)
def get_create_task(
    task_data: TaskBase,
    db: Session = Depends(settings.get_scraper_db),
    _: User = Depends(admin_only),
):
    task = TaskCRUD(db).create_task(task_data=task_data)
    return task


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(settings.get_scraper_db),
    _: User = Depends(admin_only),
):
    TaskCRUD(db).delete_task(task_id=task_id)
