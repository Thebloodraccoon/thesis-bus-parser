from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field
from typing_extensions import Annotated


class TicketDataSchema(BaseModel):
    departure_datetime: datetime
    arrival_datetime: Optional[datetime]
    from_city_id: int
    to_city_id: int
    from_station_name: Optional[str]
    to_station_name: Optional[str]
    carrier_name: str
    travel_time: Optional[timedelta]
    price: Annotated[Decimal, Field(max_digits=10, decimal_places=2)]
    currency: str = Field(max_length=5)
    available_seats: Optional[int]
    is_transfer: Optional[bool] = False
    trip_id: Optional[str] = None
