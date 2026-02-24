from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CityBase(BaseModel):
    like_bus_id: int = Field(..., description="LikeBus ID")
    name_ua: Optional[str] = Field(None, description="ua city name")
    name_en: Optional[str] = Field(None, description="en city name")
    ukrpas_id: Optional[int] = Field(None, description="UkrPass ID")
    inbus_id: Optional[int] = Field(None, description="Inbus ID")
    rubikon_id: Optional[int] = Field(None, description="Rubikon ID")
    voyager_id: Optional[int] = Field(None, description="Voyager ID")


class CityCreate(CityBase):
    pass


class CitySchema(CityBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
