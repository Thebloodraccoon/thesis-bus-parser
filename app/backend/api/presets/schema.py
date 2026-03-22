import re
import uuid
from datetime import time
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator  # type: ignore


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
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("from_cities", "to_cities", "sites")
    def validate_cities(cls, v):
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("Value must be a list")

            if not all(isinstance(city_id, (int, float)) for city_id in v):
                raise ValueError("All elements must be numbers")

            if not all(city_id > 0 for city_id in v):
                raise ValueError("City IDs must be positive numbers")

            if len(v) != len(set(v)):
                raise ValueError("Duplicate city IDs are not allowed")

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
                raise ValueError("Time must be in the format hh:mm")

            hours, minutes = map(int, v.split(":"))
            return time(hour=hours, minute=minutes)
        return v


class FilterPreset(FilterPresetBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class FilterPresetCreate(FilterPresetBase):
    pass


class FilterPresetUpdate(FilterPresetBase):
    pass
