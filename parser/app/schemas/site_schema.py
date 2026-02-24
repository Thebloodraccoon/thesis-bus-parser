from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SiteBase(BaseModel):
    """Base model for Site with common fields."""

    name: str = Field(..., description="The name of the site")
    url: str = Field(..., description="The URL of the site")
    is_active: bool = Field(True, description="Whether the site is active")

class SiteCreate(SiteBase):
    """Schema for creating a new Site."""

    pass


class SiteSchema(SiteBase):
    """Schema for reading Site data, including ID and last_parsed."""

    id: int
    last_parsed: Optional[datetime] = Field(
        None, description="The last time the site was parsed"
    )
    model_config = ConfigDict(from_attributes=True)
