from __future__ import annotations

import asyncio
import math
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

        async def _fetch_page(page: int, max_retries: int = 3) -> dict:
            for attempt in range(max_retries):
                resp = await self._get(
                    url, params={**params, "page": page}, headers=headers, timeout=120
                )

                if "application/json" in resp.headers.get("Content-Type", ""):
                    return resp.json()

                logger.warning(
                    f"[Rubikon] Non-JSON on page {page} (attempt {attempt + 1}/{max_retries}). "
                    f"Route: {departure_city.name_ua} -> {arrival_city.name_ua}"
                )
                await asyncio.sleep(2)

            raise ValueError(f"Failed to get JSON from page {page} after {max_retries} attempts.")

        all_tickets = []

        try:
            first_page_json = await _fetch_page(page=1)

            data = first_page_json.get("data", {})
            departures = data.get("departures", {})

            all_tickets.extend(departures.get("data", []))

            last_page = departures.get("last_page")

            if not last_page:
                total = data.get("departuresCount", 0)
                per_page = departures.get("per_page", 30)  # По умолчанию 30
                last_page = math.ceil(total / per_page) if per_page else 1

            if last_page > 1:
                tasks = [_fetch_page(page=p) for p in range(2, last_page + 1)]
                results = await asyncio.gather(*tasks)

                for res in results:
                    page_tickets = res.get("data", {}).get("departures", {}).get("data", [])
                    all_tickets.extend(page_tickets)

        except Exception as exc:
            raise RuntimeError(f"Fetch failed for {departure_city.name_ua} -> {arrival_city.name_ua}: {exc}") from exc

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
