import re
from datetime import datetime, time
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, field_validator, Field  # type: ignore
from pydantic_core.core_schema import ValidationInfo  # type: ignore


class TaskBase(BaseModel):
    execution_time: time = Field(
        ...,
        example="14:30",
    )
    task_name: str
    enabled: bool
    site_name: str
    start_date: int = Field(0, ge=0, description="Starting date for parsing")
    end_date: int = Field(0, ge=0, description="Ending date for parsing")
    threads: int = Field(5, ge=1, description="Number of threads to use")
    max_duration_seconds: int = Field(
        86400, ge=1, description="Maximum execution duration in seconds"
    )
    weekdays: List[int]

    @field_validator("weekdays")
    def validate_weekdays(cls, weekdays: List[int]):
        for day in weekdays:
            if not isinstance(day, int):
                raise ValueError("Each value in weekdays must be an integer")
            if day < 0 or day > 6:
                raise ValueError(
                    "weekdays must contain values between 0 and 6 inclusive"
                )
        return weekdays

    @field_validator("execution_time", mode="before")
    def validate_execution_time(cls, execution_time):
        if isinstance(execution_time, time):
            return execution_time

        if isinstance(execution_time, str):
            pattern = re.compile(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$")
            if not pattern.match(execution_time):
                raise ValueError("execution_time must be in format HH:MM (e.g., 20:22)")
            hours, minutes = map(int, execution_time.split(":"))
            return time(hour=hours, minute=minutes)

        raise ValueError(
            "execution_time must be a string in format HH:MM or a time object"
        )

    @field_validator("end_date")
    def validate_dates(cls, end_date: int, info: ValidationInfo):
        start_date = info.data.get("start_date")
        if start_date is not None:
            if start_date < -1:
                raise ValueError("start_date must be greater than -1")
            if end_date < 0:
                raise ValueError("end_date must be greater than zero")
            if end_date < start_date:
                raise ValueError("end_date cannot be less than start_date")
        return end_date


class TaskResponse(BaseModel):
    id: int
    name: str
    enabled: bool
    last_run_at: Optional[datetime] = None
    total_run_count: Optional[int] = None
    schedule_id: int
    site_id: Optional[int] = None
    start_date: Optional[int] = None
    end_date: Optional[int] = None
    threads: Optional[int] = None
    max_duration_seconds: Optional[int] = None
    weekdays: Optional[List[int]] = None
    execution_time: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
    )
