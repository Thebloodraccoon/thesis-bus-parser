import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator  # type: ignore

from app.backend.exceptions.auth_exceptions import InvalidEmailException


class UserBase(BaseModel):
    email: str
    role: Literal["admin", "analytic", "user"]

    @field_validator("email")
    def validate_email(cls, email):
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise InvalidEmailException()
        return email


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    role: Optional[Literal["admin", "analytic", "user"]] = None

    @model_validator(mode="before")
    def validate_data(cls, values):
        if not any(key for key in values if key != "id" and values[key] is not None):
            raise ValueError("At least one updatable field must be provided.")
        return values

    model_config = ConfigDict(
        json_schema_extra={"example": {"role": "user"}}
    )


class UserResponse(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
