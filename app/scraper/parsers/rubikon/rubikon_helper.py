from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from app.schemas.ticket_schema import TicketDataSchema
from app.scraper.logger import get_logger
from app.scraper.managers.http import send_request, get_response_size

logger = get_logger(__name__)


def parse_trip_data(
    trip: dict, departure_city_id: int, arrival_city_id: int
) -> Optional[TicketDataSchema]:
    try:
        departure_date = trip.get("departureDate", "")
        departure_time = trip.get("startBusStop", {}).get("time", "")

        departure_datetime_str = f"{departure_date} {departure_time}"
        departure_datetime = datetime.strptime(departure_datetime_str, "%Y-%m-%d %H:%M")

        end_bus_stop = trip.get("endBusStop", {})
        arrival_time = end_bus_stop.get("time", "")
        arrival_date = end_bus_stop.get("date", departure_date)

        if arrival_date and "." in arrival_date:
            day, month, year = arrival_date.split(".")
            arrival_date = f"{year}-{month}-{day}"

        arrival_datetime_str = f"{arrival_date} {arrival_time}"
        arrival_datetime = datetime.strptime(arrival_datetime_str, "%Y-%m-%d %H:%M")

        from_station_name = trip.get("startBusStop", {}).get("busStopName", "")
        to_station_name = trip.get("endBusStop", {}).get("busStopName", "")

        carrier_name = trip.get("carrier", {}).get("name", "")

        if "duration" in trip:
            duration = trip.get("duration", {})
            hours = duration.get("hours", 0)
            minutes = duration.get("minutes", 0)
            travel_time = timedelta(hours=hours, minutes=minutes)
        else:
            travel_time = timedelta(seconds=trip.get("wayTime", 0))

        price_raw = trip.get("priceWithDiscount", 0)
        price = Decimal(price_raw) / Decimal(100)
        currency = trip.get("currencyCode", "UAH")

        bus_changes_count = trip.get("badges", {}).get("busChangesCount", "0")
        if bus_changes_count == "1+":
            bus_changes_count = 1
        is_transfer = bus_changes_count > 0

        available_seats = trip.get("freeSeatsCount", None)

        return TicketDataSchema(
            departure_datetime=departure_datetime,
            arrival_datetime=arrival_datetime,
            from_city_id=departure_city_id,
            to_city_id=arrival_city_id,
            from_station_name=from_station_name,
            to_station_name=to_station_name,
            carrier_name=carrier_name,
            travel_time=travel_time,
            price=price,
            currency=currency,
            available_seats=available_seats,
            is_transfer=is_transfer,
        )
    except Exception as e:
        logger.error(f"Error parsing trip data: {e}")
        return None


async def get_tickets_by_page(
    url: str, params: dict, headers: dict, page: int
) -> tuple[Any, Any, Any] | None:
    try:
        page_params = {**params, "page": page}

        response = await send_request(
            url=url,
            method="GET",
            headers=headers,
            params=page_params,
            timeout=120,
            follow_redirects=True,
        )

        if response and response.status_code == 200:
            data = response.json()
            if data.get("status").endswith("success"):
                departures = data["data"]["departures"]["data"]
                departures_count = data["data"]["departuresCount"]
                return departures, departures_count, get_response_size(response)
            return None
        return None

    except Exception as e:
        raise e


async def get_all_tickets(
    url: str, params: dict, headers: dict
) -> tuple[list, float] | list:
    try:
        total_response_size = 0.0
        result: list = []

        (
            first_page_departures,
            total_departures,
            response_size,
        ) = await get_tickets_by_page(  # type: ignore
            url, params, headers, 1
        )

        total_response_size += response_size
        if first_page_departures is None:
            logger.error("Failed to fetch first page of tickets")
            return result

        result.extend(first_page_departures)
        per_page = len(first_page_departures)
        if per_page == 0:
            return result

        total_pages = (total_departures + per_page - 1) // per_page
        for page in range(2, total_pages + 1):
            departures, _, response_size = await get_tickets_by_page(
                url, params, headers, page
            )  # type: ignore
            total_response_size += response_size

            if departures is not None:
                result.extend(departures)
            else:
                logger.warning(f"Failed to fetch tickets on page {page}")

        return result, total_response_size
    except Exception as e:
        raise e
