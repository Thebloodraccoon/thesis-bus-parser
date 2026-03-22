from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CurrencySchema(BaseModel):
    """Schema for currency data validation and serialization."""

    code: str = Field(..., description="Currency code (e.g. USD, EUR)", max_length=3)
    rate: float = Field(..., description="Exchange rate value", gt=0)
    exchange_date: date = Field(
        default_factory=date.today, description="Date of exchange rate update"
    )

    @field_validator("code")
    def code_must_be_uppercase(cls, v):
        if not v or len(v) > 3:
            raise ValueError("Currency code must be 1-3 characters")
        return v.upper()

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {"code": "DZD", "rate": 0.31181, "exchange_date": "2025-04-15"}
        },
    )
