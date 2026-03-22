from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from app.parser.schemas.ticket_schema import TicketDataSchema
from app.parser.settings.logger import get_logger

logger = get_logger(__name__)


def parse_trip_data(
    trip: dict, departure_city_id: int, arrival_city_id: int
) -> Optional[TicketDataSchema]:
    try:
        departure_datetime_str = trip.get("busStopFrom", {}).get("departure", "")
        departure_datetime = datetime.strptime(
            departure_datetime_str, "%m/%d/%Y %H:%M:%S"
        )

        arrival_datetime_str = trip.get("busStopTo", {}).get("arrival", "")
        arrival_datetime = datetime.strptime(arrival_datetime_str, "%m/%d/%Y %H:%M:%S")

        from_station_name = (
            trip.get("busStopFrom", {}).get("name", "")
            + " "
            + trip.get("busStopFrom", {}).get("info", "")
        )
        to_station_name = (
            trip.get("busStopTo", {}).get("name", "")
            + " "
            + trip.get("busStopTo", {}).get("info", "")
        )

        carrier_name_str = trip.get("carrier", {}).get("name", "")
        carrier_name = carrier_name_str.split("/", 1)[1]

        travel_time_minutes = trip.get("courseInfo", {}).get("travelTime", "")
        travel_time = timedelta(minutes=float(travel_time_minutes))

        price_raw = trip.get("courseInfo", {}).get("price", "")
        price = Decimal(price_raw)
        currency = trip.get("courseInfo", {}).get("currency", "")

        available_seats = None
        is_transfer = None
        ticket = TicketDataSchema(
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

        return ticket
    except Exception as e:
        logger.error(f"Error parsing trip data: {e}")
        return None
