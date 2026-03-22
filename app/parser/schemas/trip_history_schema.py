from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Annotated


class TripHistoryBase(BaseModel):
    price: Annotated[Decimal, Field(max_digits=10, decimal_places=2)]
    currency: str
    available_seats: Optional[int] = None


class TripHistorySchema(TripHistoryBase):
    """Schema for creating a new trip history record."""


class TripHistoryCreate(TripHistoryBase):
    id: int
    trip_id: int
    model_config = ConfigDict(from_attributes=True)
