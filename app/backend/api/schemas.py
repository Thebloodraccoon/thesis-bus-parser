import re
import uuid
from datetime import date, datetime, time
from typing import List, Literal, Optional, Dict, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_core.core_schema import ValidationInfo

from app.backend.api.exceptions import InvalidEmailException


# Auth schemas
class Login(BaseModel):
    email: str
    password: str

    @field_validator("email")
    def validate_email(cls, email: str) -> str:
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise InvalidEmailException()
        return email


class TokenResponse(BaseModel):
    access_token: str


class TwoFASetupResponse(BaseModel):
    otp_uri: str
    temp_token: str


class TwoFARequiredResponse(BaseModel):
    temp_token: str


class TwoFAVerifyRequest(BaseModel):
    otp_code: str
    temp_token: str


class LogoutResponse(BaseModel):
    detail: str


# User schemas
class UserBase(BaseModel):
    email: str
    role: Literal["admin", "analytic", "user"]

    @field_validator("email")
    def validate_email(cls, email: str) -> str:
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise InvalidEmailException()
        return email


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    role: Optional[Literal["admin", "analytic", "user"]] = None

    @model_validator(mode="before")
    def validate_data(cls, values):
        if not any(key for key in values if key != "id" and values[key] is not None):
            raise ValueError("At least one updatable field must be provided.")
        return values

    model_config = ConfigDict(json_schema_extra={"example": {"role": "user"}})


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Site schemas
class SiteBase(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    is_active: Optional[bool] = True


class SiteCreate(SiteBase):
    name: str
    url: str
    is_active: bool


class SiteUpdate(SiteBase):
    name: Optional[str] = None
    url: Optional[str] = None
    is_active: Optional[bool] = None


class SiteResponse(SiteBase):
    id: int
    last_parsed: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# City schemas
class CitySchema(BaseModel):
    id: int
    like_bus_id: Optional[int] = None
    name_ua: Optional[str] = None
    name_en: Optional[str] = None


# Route / Trip schemas
class RouteSchema(BaseModel):
    id: int
    currency: str = ""
    min_price: float = 0.0
    max_price: float = 0.0
    median_price: float = 0.0
    total_segments_count: int = 0


class TripSchema(BaseModel):
    from_station: Optional[str] = None
    to_station: Optional[str] = None
    departure_date: date
    departure_time: time
    arrival_time: Optional[time] = None
    arrival_date: Optional[date] = None
    carrier_name: str
    duration: Optional[time] = None
    is_transfer: bool
    price: float
    currency: str
    available_seats: Optional[int] = None
    price_updated_at: datetime


class TripSchemaResponse(BaseModel):
    total_segments_count: int
    trips: List[TripSchema]


# Schedule schemas
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
    for part in value.split(","):
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


def validate_cron_field(value: Optional[str], field_name: str) -> Optional[str]:
    if value is None or value == "":
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


class ScheduleBase(BaseModel):
    minute: Optional[str] = Field(None)
    hour: Optional[str] = Field(None)
    day_of_week: Optional[str] = Field(None)
    day_of_month: Optional[str] = Field(None)
    month_of_year: Optional[str] = Field(None)

    _validate_minute = field_validator("minute")(
        lambda cls, v: validate_cron_field(v, "minute")
    )
    _validate_hour = field_validator("hour")(
        lambda cls, v: validate_cron_field(v, "hour")
    )
    _validate_day_of_week = field_validator("day_of_week")(
        lambda cls, v: validate_cron_field(v, "day_of_week")
    )
    _validate_day_of_month = field_validator("day_of_month")(
        lambda cls, v: validate_cron_field(v, "day_of_month")
    )
    _validate_month = field_validator("month_of_year")(
        lambda cls, v: validate_cron_field(v, "month_of_year")
    )

    @model_validator(mode="before")
    def trim_whitespaces(cls, values):
        return {k: v.strip() if isinstance(v, str) else v for k, v in values.items()}


class ScheduleCreate(ScheduleBase):
    timezone: Optional[str] = "Europe/Kiev"


class ScheduleUpdate(ScheduleBase):
    pass


class ScheduleResponse(ScheduleBase):
    id: int
    timezone: str
    model_config = ConfigDict(from_attributes=True)


# Task schemas
class TaskBase(BaseModel):
    task_name: str
    enabled: bool
    site_name: str
    start_date: int = Field(0, ge=0)
    end_date: int = Field(0, ge=0)
    threads: int = Field(5, ge=1)
    max_duration_seconds: int = Field(86400, ge=1)
    minute: str = Field(default="*")
    hour: str = Field(default="*")
    weekdays: List[int] = Field(default_factory=lambda: list(range(7)))

    @field_validator("end_date")
    def validate_dates(cls, end_date: int, info: ValidationInfo) -> int:
        start_date = info.data.get("start_date")
        if start_date is not None:
            if start_date < -1:
                raise ValueError("start_date must be greater than -1")
            if end_date < 0:
                raise ValueError("end_date must be non-negative")
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

    model_config = ConfigDict(from_attributes=True)


# Filter preset schemas
class FilterPresetBase(BaseModel):
    name: str
    from_cities: Optional[List[int]] = None
    to_cities: Optional[List[int]] = None
    sites: Optional[List[int]] = None
    is_transfer: Optional[bool] = None
    departure_from_time: Optional[time] = None
    departure_to_time: Optional[time] = None
    arrival_from_time: Optional[time] = None
    arrival_to_time: Optional[time] = None

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("from_cities", "to_cities", "sites")
    def validate_id_lists(cls, v):
        if v is not None:
            if not all(isinstance(x, (int, float)) and x > 0 for x in v):
                raise ValueError("All IDs must be positive numbers")
            if len(v) != len(set(v)):
                raise ValueError("Duplicate IDs are not allowed")
        return v

    @field_validator(
        "departure_from_time",
        "departure_to_time",
        "arrival_from_time",
        "arrival_to_time",
    )
    def validate_time_format(cls, v):
        if isinstance(v, str):
            if not re.match(r"^([0-1]?\d|2[0-3]):[0-5]\d$", v):
                raise ValueError("Time must be in format hh:mm")
            hours, minutes = map(int, v.split(":"))
            return time(hour=hours, minute=minutes)
        return v


class FilterPreset(FilterPresetBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class FilterPresetCreate(FilterPresetBase):
    pass


class FilterPresetUpdate(FilterPresetBase):
    pass
