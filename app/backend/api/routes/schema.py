from datetime import datetime, time, date
from typing import List, Optional
from pydantic import BaseModel

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

class RouteSchema(BaseModel):
    id: int
    currency: str = ""
    min_price: float = 0.0
    max_price: float = 0.0
    median_price: float = 0.0
    total_segments_count: int