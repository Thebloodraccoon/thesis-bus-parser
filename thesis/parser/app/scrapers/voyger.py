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
        resp = await self._post(
            f"{self.site.url}/Courses/CoursesList",
            json={
                "form": {
                    "adults": 1,
                    "departure": True,
                    "cityFrom": {"code": departure_city.voyager_id},
                    "cityTo": {"code": arrival_city.voyager_id},
                    "date": date.strftime("%Y-%m-%d"),
                    "agent": "VOYAGER0KK",
                    "currency": "PLN",
                }
            },
        )
        return resp.json().get("coursesList") if resp else None

    def parse(
        self,
        content: List[dict],
        departure_city: CitySchema,
        arrival_city: CitySchema,
    ) -> List[TicketData]:
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
                    is_transfer=None,
                )
                tickets.append(_to_uah(ticket, self.currencies))
            except Exception as exc:
                logger.error("Voyager trip parse error: %s", exc)

        return tickets
