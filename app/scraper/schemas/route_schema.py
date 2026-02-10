from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RouteBase(BaseModel):
    from_city_id: int = Field(..., description="ID of the departure city")
    to_city_id: int = Field(..., description="ID of the destination city")
    departure_date: date
    site_id: int = Field(..., description="ID of the site")
    parsed_at: Optional[datetime] = None


class RouteSchema(RouteBase):
    pass


class RouteCreate(RouteBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
