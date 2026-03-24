from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Annotated


# City
class CityCreate(BaseModel):
    like_bus_id: int
    name_ua: Optional[str] = None
    name_en: Optional[str] = None


class CitySchema(CityCreate):
    id: int
    ukrpas_id: Optional[int] = None
    inbus_id: Optional[int] = None
    rubikon_id: Optional[int] = None
    voyager_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# Currency
class CurrencySchema(BaseModel):
    code: str = Field(..., max_length=3)
    rate: float = Field(..., gt=0)
    exchange_date: date = Field(default_factory=date.today)

    model_config = ConfigDict(from_attributes=True)


# Route / Trip / History
class RouteSchema(BaseModel):
    site_id: int
    from_city_id: int
    to_city_id: int
    departure_date: date
    parsed_at: Optional[datetime] = None


class TripSchema(BaseModel):
    from_station: Optional[str] = None
    to_station: Optional[str] = None
    departure_time: time
    arrival_time: Optional[time] = None
    arrival_date: Optional[date] = None
    carrier_name: str
    duration: Optional[timedelta] = None
    is_transfer: bool = False


class TripHistorySchema(BaseModel):
    price: Annotated[Decimal, Field(max_digits=10, decimal_places=2)]
    currency: str
    available_seats: Optional[int] = None


# Internal ticket DTO (intermediate between raw scrape and DB schemas)
class TicketData(BaseModel):
    """
    Unified ticket representation returned by every scraper's *parse* method.
    The orchestrator converts it to RouteSchema / TripSchema / TripHistorySchema.
    """

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
    is_transfer: bool = False

class RouteData(BaseModel):
    """One scraping task: a city pair for a specific date."""

    departure_city: CitySchema
    arrival_city: CitySchema
    route_id: int
    trip_id: str
    from_date: datetime
    to_date: datetime
    departure_station_id: Optional[int] = None
    arrival_station_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)