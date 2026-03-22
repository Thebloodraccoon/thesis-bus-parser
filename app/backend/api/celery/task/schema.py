from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, field_validator, Field  # type: ignore
from pydantic_core.core_schema import ValidationInfo  # type: ignore


class TaskBase(BaseModel):
    task_name: str
    enabled: bool
    site_name: str
    start_date: int = Field(0, ge=0, description="Starting date for parsing")
    end_date: int = Field(0, ge=0, description="Ending date for parsing")
    threads: int = Field(5, ge=1, description="Number of threads to use")
    max_duration_seconds: int = Field(
        86400, ge=1, description="Maximum execution duration in seconds"
    )
    minute: str = Field(default="*", example="*/15")
    hour: str = Field(default="*", example="9,21")
    weekdays: List[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6])

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
    minute: Optional[str] = None
    hour: Optional[str] = None
    weekdays: Optional[List[int]] = None

    model_config = ConfigDict(
        from_attributes=True,
    )
