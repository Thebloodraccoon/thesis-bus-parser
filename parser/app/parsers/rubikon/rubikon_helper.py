from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from parser.app.schemas.ticket_schema import TicketDataSchema
from parser.app.settings.logger import get_logger

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
