from pydantic import BaseModel, ConfigDict  # type: ignore
from typing import Optional
from datetime import datetime


class SiteBase(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    is_active: Optional[bool] = True
    api_key: Optional[str] = None
    is_aggregator: Optional[bool] = False


class SiteCreate(SiteBase):
    name: str
    url: str
    is_active: bool
    is_aggregator: bool


class SiteUpdate(SiteBase):
    name: Optional[str] = None
    url: Optional[str] = None
    is_active: Optional[bool] = None
    api_key: Optional[str] = None
    is_aggregator: Optional[bool] = None


class SiteResponse(SiteBase):
    id: int
    last_parsed: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
