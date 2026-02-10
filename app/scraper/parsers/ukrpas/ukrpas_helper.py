from datetime import datetime
from decimal import ROUND_DOWN, Decimal
from typing import Optional

from app.schemas.ticket_schema import TicketDataSchema
from app.scraper.logger import get_logger

logger = get_logger(__name__)


def parse_trip_data(
    trip: dict, departure_city_id: int, arrival_city_id: int
) -> Optional[TicketDataSchema]:
    try:
        # Validate and fetch the first route segment
        route_segment = trip.get("route", [{}])[0]
        if not route_segment:
            raise ValueError("Route segment is missing or empty.")

        # Parse datetime fields
        departure_datetime_str = route_segment.get("departure_date_time", "")
        arrival_datetime_str = route_segment.get("arrival_date_time", "")

        try:
            departure_datetime = datetime.strptime(
                departure_datetime_str, "%Y-%m-%d %H:%M"
            )
        except Exception:
            logger.error(f"Error parsing departure datetime: {departure_datetime_str}")
            departure_datetime = None

        try:
            arrival_datetime = datetime.strptime(arrival_datetime_str, "%Y-%m-%d %H:%M")
        except Exception:
            logger.warning(f"Error parsing arrival datetime: {arrival_datetime_str}")
            arrival_datetime = None

        # Parse station names
        points = route_segment.get("route", [])
        if not points or len(points) < 2:
            raise ValueError("Invalid route points data.")

        from_station = points[0].get("point", {})
        to_station = points[-1].get("point", {})
        from_station_name = (
            from_station.get("name", "") + " " + from_station.get("address", "")
        ).strip()
        to_station_name = (
            to_station.get("name", "") + " " + to_station.get("address", "")
        ).strip()

        # Parse carrier name
        carrier_name = route_segment.get("carrier", {}).get("name", "Unknown")

        # Calculate travel time
        travel_time = None
        if departure_datetime and arrival_datetime:
            travel_time = arrival_datetime - departure_datetime

        # Parse pricing data
        price_data = trip.get("price", {})
        price_raw = price_data.get("total", 0)
        price = Decimal(price_raw) / Decimal("100").quantize(
            Decimal("0.01"), rounding=ROUND_DOWN
        )
        currency = price_data.get("currency", "Unknown")

        # Parse seat availability and transfer info
        available_seats = trip.get("free_seats", 0)
        is_transfer = bool(trip.get("trip_transfers"))

        # Build and return ticket data
        ticket_data = TicketDataSchema(
            departure_datetime=departure_datetime,  # type: ignore
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
        return ticket_data

    except Exception as e:
        logger.error(f"Error parsing trip data: {e}")
        raise e
