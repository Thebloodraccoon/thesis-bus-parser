from datetime import datetime, time, date
from typing import List, Optional  # type: ignore

from pydantic import BaseModel  # type: ignore


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
    our_segments_count: int
    competitor_segments_count: int

    our_trips: List[TripSchema]
    competitor_trips: List[TripSchema]


class RouteSchema(BaseModel):
    id: int
    currency: str = ""
    our_min_price: float = 0.0
    our_max_price: float = 0.0
    competitor_min_price: float = 0.0
    competitor_max_price: float = 0.0
    median_price: float = 0.0
    our_segments_count: int
    competitor_segments_count: int
