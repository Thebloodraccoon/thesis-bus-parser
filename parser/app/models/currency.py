from sqlalchemy import Column, Date, Float, Integer, String
from sqlalchemy.orm import validates

from parser.app.settings.conf import Base


class CurrencyModel(Base):
    __tablename__ = "currency"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(
        String,
        unique=True,
        index=True,
        nullable=False,
        comment="Currency code (e.g. DZD)",
    )
    rate = Column(Float, nullable=False, comment="Exchange rate value")
    exchange_date = Column(Date, nullable=True, comment="Date of exchange rate update")

    @validates("code")
    def validate_code(self, key, code):
        if not code or len(code) > 3:
            raise ValueError("Currency code must be 1-3 characters")
        return code.upper()

    def __repr__(self):
        return (
            f"<Currency(code={self.code}, rate={self.rate}, date={self.exchange_date})>"
        )
