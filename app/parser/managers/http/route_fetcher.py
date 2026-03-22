import random
from datetime import datetime
from typing import List, Dict, Any

import httpx
from sqlalchemy.orm import Session
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from app.parser.db.city_db import city_crud
from app.parser.schemas.types import RouteData
from app.parser.settings.conf import get_db
from app.parser.settings.logger import get_logger
from app.parser.settings import settings

logger = get_logger(__name__)


class RouteFetcher:
    @classmethod
    def get_routes(cls, date: datetime) -> List[RouteData]:
        """Gets the routes, converts them to RouteData, and shuffles them."""

        with get_db() as db:
            all_routes_data = cls._get_routes_from_api(date)

            route_data_list: List[RouteData] = []

            for route in all_routes_data:
                try:
                    processed_dict = cls._process_route_data(route, db)

                    if not processed_dict.get("from") or not processed_dict.get("to"):
                        logger.warning(f"City not found in DB for route {route.get('route_id')}")
                        continue

                    route_obj = RouteData(
                        departure_city=processed_dict.get("from"),
                        arrival_city=processed_dict.get("to"),
                        route_id=processed_dict.get("route_id"),
                        trip_id=[str(processed_dict.get("trip_id"))],
                        from_date=processed_dict.get("from_date"),
                        to_date=processed_dict.get("to_date"),
                        departure_station_id=processed_dict.get("departure_station_id"),
                        arrival_station_id=processed_dict.get("arrival_station_id"),
                    )
                    route_data_list.append(route_obj)
                except Exception as e:
                    logger.error(f"Failed to process route to RouteData: {e}")

            random.shuffle(route_data_list)

            return route_data_list

    @classmethod
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(60),
        retry=retry_if_exception_type((Exception, ValueError)),
        reraise=True,
    )
    def _get_routes_from_api(cls, date: datetime) -> List[Dict[str, Any]]:
        """Fetch routes with retry logic on failure."""
        date_str = date.strftime("%Y-%m-%d")
        routes_endpoint = "https://likebus.ua/sync/v3/routes/dayInfoTesting"

        response = httpx.get(
            routes_endpoint,
            headers={"X-API-KEY": settings.API_KEY},
            params={"date": date_str},
            timeout=30,
        )

        routes_data = response.json().get("list", [])
        if not routes_data:
            logger.warning(f"No routes returned from API for date {date_str}")

        return routes_data

    @classmethod
    def _process_route_data(cls, route: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Auxiliary method for obtaining cities and dates"""

        from_city_obj = city_crud.get_city_by_like_bus_id(db, route["departure_city_id"])
        to_city_obj = city_crud.get_city_by_like_bus_id(db, route["arrival_city_id"])

        dep_time_str = str(route["departure_time"]).strip()
        arr_time_str = str(route["arrival_time"]).strip()

        if len(dep_time_str) <= 10:
            dep_time_str += " 00:00:00"
        if len(arr_time_str) <= 10:
            arr_time_str += " 00:00:00"

        from_date = datetime.strptime(dep_time_str, "%Y-%m-%d %H:%M:%S")
        to_date = datetime.strptime(arr_time_str, "%Y-%m-%d %H:%M:%S")

        return {
            "departure_station_id": route.get("departure_station_id"),
            "arrival_station_id": route.get("arrival_station_id"),
            "trip_id": route["trip_id"],
            "route_id": route["route_id"],
            "from": from_city_obj,
            "to": to_city_obj,
            "from_date": from_date,
            "to_date": to_date,
        }