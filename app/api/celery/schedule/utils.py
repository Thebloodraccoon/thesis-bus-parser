from typing import List, Optional, Union

from fastapi import HTTPException, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.api.celery.utils import update_celery_cache
from app.exceptions.scraper_exceptions import ScheduleNotFound



class ScheduleCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_schedule_by_id(self, schedule_id: int) -> Optional[CeleryScheduleModel]:
        schedule = (
            self.db.query(CeleryScheduleModel)
            .filter(CeleryScheduleModel.id == schedule_id)
            .first()
        )
        if not schedule:
            raise ScheduleNotFound(schedule_id)

        return schedule

    def update_schedule(
        self,
        schedule_id: int,
        schedule_data: ScheduleUpdate,
    ) -> CeleryScheduleModel:
        schedule_to_update = self.get_schedule_by_id(schedule_id)

        update_data = schedule_data.model_dump(exclude_unset=True)
        update_data = {key: value for key, value in update_data.items() if value != ""}
        for key, value in update_data.items():
            setattr(schedule_to_update, key, value)

        self.db.commit()
        self.db.refresh(schedule_to_update)

        update_celery_cache(db=self.db)
        return schedule_to_update

    def create_schedule(self, schedule_data: ScheduleCreate) -> CeleryScheduleModel:
        created_schedule = CeleryScheduleModel(**schedule_data.model_dump())
        self.db.add(created_schedule)
        self.db.commit()
        self.db.refresh(created_schedule)

        return created_schedule

    def delete_schedule(self, schedule_id: int) -> None:
        schedule_to_delete = (
            self.db.query(CeleryScheduleModel)
            .filter(CeleryScheduleModel.id == schedule_id)
            .first()
        )

        if not schedule_to_delete:
            raise ScheduleNotFound(schedule_id)

        self.db.delete(schedule_to_delete)
        self.db.commit()
