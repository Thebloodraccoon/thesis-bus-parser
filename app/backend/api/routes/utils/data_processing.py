from datetime import date, time, timedelta
from typing import List, Any, Dict, Set

from app.backend.api.routes.schema import RouteSchema, TripSchemaResponse, TripSchema



def convert_timedelta_to_time(td: timedelta) -> time | None:
    if td is None:
        return None

    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return time(hours % 24, minutes, seconds)


def process_routes_result(result) -> dict[Any, RouteSchema]:
    site_route_dict = {}

    for route_data in result:
        site_id = route_data.site_id
        route_id = route_data.id

        if site_id not in site_route_dict:
            site_route_dict[site_id] = {}

        route_schema = RouteSchema(
            id=route_id,
            currency=route_data.currency or "",
            min_price=route_data.min_price or 0.0,
            max_price=route_data.max_price or 0.0,
            median_price=route_data.median_price or 0.0,
            total_segments_count=route_data.total_segments_count or 0,
        )

        site_route_dict[site_id] = route_schema

    return site_route_dict


def process_trips_result(result) -> TripSchemaResponse:
    trips = []

    for trip_data in result:
        trip_model = trip_data[0]
        route_date = trip_data.route_date

        trip_schema = TripSchema(
            from_station=trip_model.from_station,
            to_station=trip_model.to_station,
            departure_date=route_date,
            departure_time=trip_model.departure_time,
            arrival_time=trip_model.arrival_time,
            arrival_date=trip_model.arrival_date,
            carrier_name=trip_model.carrier_name,
            duration=convert_timedelta_to_time(trip_model.duration),
            is_transfer=trip_model.is_transfer,
            price=trip_data.price,
            currency=trip_data.currency,
            available_seats=trip_data.available_seats,
            price_updated_at=trip_data.price_updated_at,
        )
        trips.append(trip_schema)

    return TripSchemaResponse(
        total_segments_count=len(trips),
        trips=trips,
    )


def create_route_entry(
    from_city_id: int,
    to_city_id: int,
    departure_date: date,
    available_sites: List[str],
    existing_sites: List[str],
) -> Dict[str, Any]:
    route_entry: Dict[str, Any] = {
        "from_city": from_city_id,
        "to_city": to_city_id,
        "departure_date": str(departure_date),
        "agents": {},
    }
    existing_sites = [str(site) for site in existing_sites]

    for site_id in available_sites:
        if site_id in existing_sites:
            route_entry["agents"][site_id] = {}
        else:
            route_entry["agents"][site_id] = {
                "status": f"site with ID {site_id} does not exist"
            }

    return route_entry


def initialize_route_by_cities_result(
    from_city_id: int,
    to_city_id: int,
    departure_dates: List[date],
    available_sites: List[str],
    existing_sites_str: Set[str],
) -> Dict[str, Any]:
    date_strings = [str(d) for d in departure_dates]
    result: Dict[str, Any] = {
        "from_city": from_city_id,
        "to_city": to_city_id,
        "agents": {},
    }

    for site_id in available_sites:
        site_id_str = str(site_id)

        if site_id_str not in existing_sites_str:
            result["agents"][site_id_str] = {
                "status": f"site with ID {site_id} does not exist",
            }
        else:
            result["agents"][site_id_str] = {date_str: {} for date_str in date_strings}

    return result


def add_route_for_date(
    result: Dict[str, Any], routes: Dict[int, Any], date_str: str
) -> None:
    for site_id, route_obj in routes.items():
        site_id_str = str(site_id)
        if site_id_str not in result["agents"]:
            continue

        site_data = result["agents"][site_id_str]
        if not isinstance(site_data, dict) or "status" in site_data:
            continue

        site_data[date_str] = route_obj
