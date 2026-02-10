from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, Optional

from app.settings.conf import get_db
from app.scraper.db.currency_db import get_currency_by_code
from app.scraper.schemas.ticket_schema import TicketDataSchema
from app.settings.logger import logger


def convert_ticket_to_uah(
    ticket: TicketDataSchema, currencies: Dict[str, float]
) -> TicketDataSchema:
    if ticket.currency == "UAH":
        return ticket

    try:
        currency_rate = get_currency_rate(ticket.currency, currencies)
        if currency_rate is None:
            raise ValueError(f"Currency rate not found for {ticket.currency}")

        converted_price = (ticket.price * Decimal(str(currency_rate))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        ticket.price = converted_price
        ticket.currency = "UAH"
        return ticket

    except Exception as e:
        raise ValueError(
            f"Error converting ticket currency from {ticket.currency} to UAH: {e}"
        )


def get_currency_rate(
    currency_code: str, currencies: Dict[str, float]
) -> Optional[float]:
    if currency_code in currencies and currencies.get(currency_code):
        return currencies[currency_code]

    if currency_code == "UAH":
        return 1.0

    with get_db() as db:
        currency = get_currency_by_code(db, currency_code)

        if currency:
            rate = float(currency.rate)
            currencies[currency_code] = rate

            return rate
        else:
            logger.error(f"No found currency for code {currency_code}")
            return None

