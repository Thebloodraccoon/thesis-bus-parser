from pydantic import BaseModel  # type: ignore
from typing import Optional, List  # type: ignore


class CitySchema(BaseModel):
    id: int
    like_bus_id: Optional[int] = None
    name_ua: Optional[str] = None
    name_en: Optional[str] = None
