from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from bs4 import BeautifulSoup

from app.parser.managers.http import send_request, get_response_size
from app.parser.schemas.city_schema import CitySchema
from app.parser.schemas.ticket_schema import TicketDataSchema
from app.parser.settings.logger import get_logger

logger = get_logger(__name__)


def parse_trip_data(
    trip: dict, departure_city: CitySchema, arrival_city: CitySchema
) -> Optional[TicketDataSchema]:
    try:
        departure_str = trip.get("departure", "")
        arrival_str = trip.get("arrival", "")
        if not departure_str or not arrival_str:
            logger.error("Missing departure or arrival datetime")
            return None

        departure_datetime = datetime.strptime(departure_str, "%Y-%m-%d %H:%M")
        arrival_datetime = datetime.strptime(arrival_str, "%Y-%m-%d %H:%M")

        from_station_name = departure_city.city_ua
        to_station_name = arrival_city.city_ua
        carrier_name = trip.get("transporter", {}).get("name", "")

        price_raw = trip.get("cost", {}).get("min")
        if price_raw is None:
            logger.error("Price is missing")
            return None
        price = Decimal(str(price_raw)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        travel_time = arrival_datetime - departure_datetime
        currency = trip.get("cost", {}).get("currency", {}).get("alpha3", "")
        available_seats = trip.get("free_seats", 0)
        is_transfer = trip.get("transit", False)

        ticket_data = TicketDataSchema(
            departure_datetime=departure_datetime,
            arrival_datetime=arrival_datetime,
            from_city_id=departure_city.id,
            to_city_id=arrival_city.id,
            from_station_name=from_station_name,
            to_station_name=to_station_name,
            carrier_name=carrier_name,
            travel_time=travel_time,
            price=price,
            currency=currency,
            available_seats=available_seats,
            is_transfer=is_transfer,
        )

        return ticket_data

    except Exception as e:
        logger.error(f"Error parsing trip data: {e}")
        raise e


async def get_request_url():
    site = await send_request("https://inbus.ua/", "GET")
    response_size = get_response_size(site)

    if site.status_code == 200:
        soup = BeautifulSoup(site.text, "html.parser")

        scripts = soup.find_all("script", src=True)

        for script in scripts:
            src = script["src"]
            if "/_next/static/" in src and "_buildManifest.js" in src:
                token = src.split("/_next/static/")[1].split("/_buildManifest.js")[0]
                return token, response_size

        raise ValueError("Token not found in the page scripts.")

    raise Exception(f"Failed to fetch site. Status code: {site.status_code}")


async def get_cookies(url: str):
    response = await send_request(
        url,
        "GET",
    )
    if response is None:
        return {}

    cookies = response.cookies
    return cookies, get_response_size(response)
