import re
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, Optional

from app.parser.db.city_db import logger
from app.parser.db.currency_db import get_currency_by_code
from app.parser.managers.http import send_request, get_response_size
from app.parser.schemas.ticket_schema import TicketDataSchema
from app.parser.settings.conf import get_db


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


async def get_ray_hash(url: str, data: dict, cookies=None) -> tuple[str, Any]:
    """Sends a POST request to the specified URL with the given form data and extracts the 'ray' hash from the HTML response."""

    response = await send_request(
        url=url,
        method="POST",
        data=data,
        follow_redirects=True,
        timeout=240,
        cookies=cookies,
    )
    size = get_response_size(response)
    ray = extract_ray_hash(response.text)
    if not ray:
        logger.warning("Ray hash not found in response text.")

    return ray, size


def extract_ray_hash(text: str) -> str:
    """Extracts the 'ray' hash value from the given HTML text using a regular expression."""

    ray_pattern = r'data-url=["\'].*?ray=([^"\']+)["\']'
    match = re.search(ray_pattern, text)

    if match:
        return match.group(1)

    return ""
