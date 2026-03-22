from datetime import date, time, timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TripBase(BaseModel):
    from_station: Optional[str] = None
    to_station: Optional[str] = None
    departure_time: time
    arrival_time: Optional[time] = None
    arrival_date: Optional[date] = None
    carrier_name: str
    duration: Optional[timedelta] = None
    is_transfer: bool = False


class TripSchema(TripBase):
    """Schema for creating a new trip."""


class TripCreate(TripBase):
    id: int
    route_id: int
    model_config = ConfigDict(from_attributes=True)
