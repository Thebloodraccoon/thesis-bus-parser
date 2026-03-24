from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, List

from thesis.parser.app.schemas import CitySchema, TicketData
from thesis.parser.app.scrapers.base import RequestScraper, _to_uah, logger


class RubikonScraper(RequestScraper):
    """Scraper for rubikon.com.ua (paginated JSON API)."""

    @classmethod
    async def create(cls) -> "RubikonScraper":
        return cls(await cls._load_site("rubikon"))

    async def fetch(
        self,
        date: datetime,
        departure_city: CitySchema,
        arrival_city: CitySchema,
        **_: Any,
    ) -> List[dict]:
        url = f"{self.site.url}/departures"
        params = {
            "departureDate": date.strftime("%Y-%m-%d"),
            "passengers[adults][count]": 1,
            "currencyId": 18,
            "from[id]": departure_city.rubikon_id,
            "to[id]": arrival_city.rubikon_id,
        }
        headers = {"authorization": "", "cache-control": "no-cache", "lang": "uk"}

        page, all_tickets = 1, []
        while True:
            resp = await self._get(
                url, params={**params, "page": page}, headers=headers, timeout=120
            )
            data = resp.json().get("data", {})
            tickets = data.get("departures", {}).get("data", [])
            total = data.get("departuresCount", 0)
            all_tickets.extend(tickets)
            if len(all_tickets) >= total or not tickets:
                break
            page += 1
        return all_tickets

    def parse(
        self,
        content: List[dict],
        departure_city: CitySchema,
        arrival_city: CitySchema,
    ) -> List[TicketData]:
        tickets: List[TicketData] = []
        for trip in content:
            try:
                dep_date = trip.get("departureDate", "")
                dep_time = trip.get("startBusStop", {}).get("time", "")
                dep_dt = datetime.strptime(f"{dep_date} {dep_time}", "%Y-%m-%d %H:%M")

                end = trip.get("endBusStop", {})
                arr_time = end.get("time", "")
                arr_date = end.get("date", dep_date)
                if "." in arr_date:
                    d, m, y = arr_date.split(".")
                    arr_date = f"{y}-{m}-{d}"
                arr_dt = datetime.strptime(f"{arr_date} {arr_time}", "%Y-%m-%d %H:%M")

                dur_raw = trip.get("duration", {})
                duration = (
                    timedelta(
                        hours=dur_raw.get("hours", 0), minutes=dur_raw.get("minutes", 0)
                    )
                    if dur_raw
                    else timedelta(seconds=trip.get("wayTime", 0))
                )

                price = Decimal(trip.get("priceWithDiscount", 0)) / 100
                bc = trip.get("badges", {}).get("busChangesCount", "0")
                transfer = int(bc) > 0 if str(bc).isdigit() else True

                ticket = TicketData(
                    departure_datetime=dep_dt,
                    arrival_datetime=arr_dt,
                    from_city_id=departure_city.id,
                    to_city_id=arrival_city.id,
                    from_station_name=trip.get("startBusStop", {}).get("busStopName"),
                    to_station_name=trip.get("endBusStop", {}).get("busStopName"),
                    carrier_name=trip.get("carrier", {}).get("name", ""),
                    travel_time=duration,
                    price=price,
                    currency=trip.get("currencyCode", "UAH"),
                    available_seats=trip.get("freeSeatsCount"),
                    is_transfer=transfer,
                )
                tickets.append(_to_uah(ticket, self.currencies))
            except Exception as exc:
                logger.error("Rubikon trip parse error: %s", exc)

        return tickets
