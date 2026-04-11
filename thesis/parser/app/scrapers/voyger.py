from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional, List

from thesis.parser.app.schemas import TicketData, CitySchema
from thesis.parser.app.scrapers.base import RequestScraper, _to_uah, logger


class VoyagerScraper(RequestScraper):
    """Scraper for voyager.pl (POST JSON API, prices in PLN)."""

    @classmethod
    async def create(cls) -> "VoyagerScraper":
        return cls(await cls._load_site("voyager"))

    async def fetch(
        self,
        date: datetime,
        departure_city: CitySchema,
        arrival_city: CitySchema,
        **_: Any,
    ) -> Optional[List[dict]]:
        date_str = date.strftime("%Y-%m-%d")
        logger.debug(
            f"[Voyager] Fetching tickets: {departure_city.name_ua} -> {arrival_city.name_ua} for {date_str}"
        )

        try:
            resp = await self._post(
                f"{self.site.url}/Courses/CoursesList",
                json={
                    "form": {
                        "adults": 1,
                        "departure": True,
                        "cityFrom": {"code": departure_city.voyager_id},
                        "cityTo": {"code": arrival_city.voyager_id},
                        "date": date_str,
                        "agent": "VOYAGER0KK",
                        "currency": "PLN",
                    }
                },
            )
            data = resp.json().get("coursesList") if resp else None
            count = len(data) if data else 0

            logger.info(
                f"[Voyager] Fetched {count} raw trips for {departure_city.name_ua} -> {arrival_city.name_ua}"
            )
            return data

        except Exception as exc:
            logger.error(
                f"[Voyager] Fetch HTTP/JSON error for {departure_city.name_ua} -> {arrival_city.name_ua}: {exc}"
            )
            return None

    def parse(
        self,
        content: List[dict],
        departure_city: CitySchema,
        arrival_city: CitySchema,
    ) -> List[TicketData]:
        logger.debug(f"[Voyager] Starting parse of {len(content)} trips...")
        tickets: List[TicketData] = []

        for trip in content:
            try:
                dep_dt = datetime.strptime(
                    trip["busStopFrom"]["departure"], "%m/%d/%Y %H:%M:%S"
                )
                arr_dt = datetime.strptime(
                    trip["busStopTo"]["arrival"], "%m/%d/%Y %H:%M:%S"
                )
                carrier_raw = trip.get("carrier", {}).get("name", "")
                carrier = (
                    carrier_raw.split("/", 1)[1] if "/" in carrier_raw else carrier_raw
                )

                ticket = TicketData(
                    departure_datetime=dep_dt,
                    arrival_datetime=arr_dt,
                    from_city_id=departure_city.id,
                    to_city_id=arrival_city.id,
                    from_station_name=(
                        f"{trip['busStopFrom'].get('name', '')} "
                        f"{trip['busStopFrom'].get('info', '')}".strip()
                    ),
                    to_station_name=(
                        f"{trip['busStopTo'].get('name', '')} "
                        f"{trip['busStopTo'].get('info', '')}".strip()
                    ),
                    carrier_name=carrier,
                    travel_time=timedelta(
                        minutes=float(trip["courseInfo"].get("travelTime", 0))
                    ),
                    price=Decimal(str(trip["courseInfo"].get("price", 0))),
                    currency=trip["courseInfo"].get("currency", "PLN"),
                    available_seats=None,
                    is_transfer=False,
                )
                tickets.append(_to_uah(ticket, self.currencies))

            except Exception as exc:
                logger.error(f"[Voyager] Parse error: {exc}. Raw trip data: {trip}")

        if tickets:
            logger.info(
                f"[Voyager] Successfully parsed {len(tickets)}/{len(content)} tickets."
            )

        return tickets
