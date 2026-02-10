from typing import Optional, Dict, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator  # type: ignore


def _validate_star_or_step(value: str, field_name: str) -> Optional[str]:
    if value == "*":
        return value
    if value.startswith("*/"):
        try:
            step = int(value[2:])
            if step <= 0:
                raise ValueError(f"Step value in '{value}' must be positive")
        except ValueError:
            raise ValueError(f"Invalid step format in '{value}' for {field_name}")
        return value
    return None


def _validate_range_or_number(
    value: str, field_name: str, min_val: int, max_val: int
) -> str:
    parts = value.split(",")
    for part in parts:
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                if not (min_val <= start <= end <= max_val):
                    raise ValueError(
                        f"Range '{part}' for {field_name} must be between {min_val} and {max_val}"
                    )
            except ValueError:
                raise ValueError(f"Invalid range format in '{part}' for {field_name}")
        else:
            try:
                num = int(part)
                if not (min_val <= num <= max_val):
                    raise ValueError(
                        f"Value '{num}' for {field_name} must be between {min_val} and {max_val}"
                    )
            except ValueError:
                raise ValueError(f"Invalid value format in '{part}' for {field_name}")
    return value


def validate_cron_field(
    value: Optional[str], field_name: str, allow_empty: bool = False
) -> Optional[str]:
    if value is None or value == "":
        if allow_empty:
            return ""
        raise ValueError(f"Field {field_name} cannot be empty")

    ranges: Dict[str, Tuple[int, int]] = {
        "minute": (0, 59),
        "hour": (0, 23),
        "day_of_week": (0, 6),
        "day_of_month": (1, 31),
        "month_of_year": (1, 12),
    }
    min_val, max_val = ranges.get(field_name, (0, 59))

    if (result := _validate_star_or_step(value, field_name)) is not None:
        return result

    return _validate_range_or_number(value, field_name, min_val, max_val)


CRON_EXAMPLE = {
    "minute": "*/15",
    "hour": "9-17",
    "day_of_week": "1-5",
    "day_of_month": "*",
    "month_of_year": "*",
}


class ScheduleBase(BaseModel):
    minute: Optional[str] = Field(
        None,
        description="Minutes (0-59). Accepts: Numbers (15), Lists (5,10,15), Ranges (0-30), Steps*/15",
    )
    hour: Optional[str] = Field(
        None,
        description="Hours (0-23). Accepts: Numbers (9), Lists (9,12,15), Ranges (9-17), Steps*/3",
    )
    day_of_week: Optional[str] = Field(
        None,
        description="Day of the week (0-6, where 0 = Sunday). Accepts: Numbers (1), Lists (1,3,5), Ranges (1-5), *",
    )
    day_of_month: Optional[str] = Field(
        None,
        description="Day of the month (1-31). Accepts: Numbers (15), Lists (1,15,30), Ranges (1-15), *",
    )
    month_of_year: Optional[str] = Field(
        None,
        description="Month (1-12). Accepts: Numbers (3), Lists (3,6,9), Ranges (3-6), *",
    )

    _validate_minute = field_validator("minute")(
        lambda cls, v: validate_cron_field(v, "minute", allow_empty=False)
    )
    _validate_hour = field_validator("hour")(
        lambda cls, v: validate_cron_field(v, "hour", allow_empty=False)
    )
    _validate_day_of_week = field_validator("day_of_week")(
        lambda cls, v: validate_cron_field(v, "day_of_week", allow_empty=False)
    )
    _validate_day_of_month = field_validator("day_of_month")(
        lambda cls, v: validate_cron_field(v, "day_of_month", allow_empty=False)
    )
    _validate_month_of_year = field_validator("month_of_year")(
        lambda cls, v: validate_cron_field(v, "month_of_year", allow_empty=False)
    )

    @model_validator(mode="before")
    def trim_whitespaces(cls, values):
        for field in values:
            if isinstance(values[field], str):
                values[field] = values[field].strip()
        return values


class ScheduleUpdate(ScheduleBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": CRON_EXAMPLE,
            "description": "Обновление расписания",
        }
    )


class ScheduleCreate(ScheduleUpdate):
    timezone: Optional[str] = "Europe/Kiev"

    model_config = ConfigDict(
        json_schema_extra={
            "example": CRON_EXAMPLE,
            "description": "Creating a Schedule",
        }
    )


class ScheduleResponse(ScheduleBase):
    id: int
    timezone: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "day_of_week": "1-5",
                "day_of_month": "*",
                "hour": "9-17",
                "minute": "*/15",
                "month_of_year": "*",
                "id": 1,
                "timezone": "Europe/Kiev",
            }
        },
    )
