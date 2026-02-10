import random
from datetime import datetime
from typing import List, Dict, Any

import httpx
from sqlalchemy.orm import Session
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from app.scraper.db.city_db import city_crud
from app.scraper.schemas.types import RouteData
from app.settings.conf import get_db
from app.settings.logger import get_logger

logger = get_logger(__name__)


class LikeBusRouteFetcher:
    def get_routes(self, date: datetime, site) -> List[RouteData]:
        """Gets the routes, converts them to RouteData, and shuffles them."""

        with get_db() as db:
            all_routes_data = self._fetch_routes_from_all_hosts(hosts, date)

            route_data_list: List[RouteData] = []

            for route in all_routes_data:
                try:
                    processed_dict = self._process_route_data(route, db)

                    route_obj = RouteData(
                        departure_city=processed_dict.get("from"),
                        arrival_city=processed_dict.get("to"),
                        route_id=processed_dict.get("route_id"),
                        trip_id=processed_dict.get("trip_id"),
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
    def _build_host_list(cls, site) -> List[Dict[str, str]]:
        hosts = []
        if site.api_key:
            hosts.append({"host": "likebus.ua", "api_key": site.api_key})

        additional_hosts = get_hosts_by_site_id(site.id)
        for host_model in additional_hosts:
            clean_host = host_model.host_url.replace("https://", "").replace(
                "http://", ""
            )
            hosts.append({"host": clean_host, "api_key": host_model.api_key})
        return hosts

    def _fetch_routes_from_all_hosts(
        self, hosts: List[Dict[str, str]], date: datetime
    ) -> List[Dict[str, Any]]:
        all_routes_data = []
        for host_info in hosts:
            try:
                logger.info(f"Getting routes from host: {host_info['host']}")
                routes_data = self._get_routes_from_host(
                    date, host_info["host"], host_info["api_key"]
                )
                all_routes_data.extend(routes_data)
                logger.info(f"Got {len(routes_data)} routes from {host_info['host']}")
            except Exception as e:
                logger.error(f"Failed to get routes from {host_info['host']}: {e}")
        return all_routes_data

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(60),
        retry=retry_if_exception_type((Exception, ValueError)),
        reraise=True,
    )
    def _get_routes_from_host(
        self, date: datetime, host: str, api_key: str
    ) -> List[Dict[str, Any]]:
        date_str = date.strftime("%Y-%m-%d")
        routes_endpoint = f"https://{host}/sync/v3/routes/dayInfoTesting"

        response = httpx.get(
            routes_endpoint,
            headers={"X-API-KEY": api_key},
            params={"date": date_str},
            timeout=30,
        )

        routes_data = response.json().get("list", [])
        if not routes_data:
            logger.warning(f"No routes returned from {host} API for date {date_str}")

        return routes_data

    @classmethod
    def _process_route_data(cls, route: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Auxiliary method for obtaining cities and dates"""

        from_city = city_crud.get_city_by_like_bus_id(db, route["departure_city_id"])
        to_city = city_crud.get_city_by_like_bus_id(db, route["arrival_city_id"])

        from_date = datetime.strptime(route["departure_time"], "%Y-%m-%d %H:%M:%S")
        to_date = datetime.strptime(route["arrival_time"], "%Y-%m-%d %H:%M:%S")

        return {
            "departure_station_id": route["departure_station_id"],
            "arrival_station_id": route["arrival_station_id"],
            "trip_id": route["trip_id"],
            "route_id": route["route_id"],
            "from": from_city,
            "to": to_city,
            "from_date": from_date,
            "to_date": to_date,
        }
