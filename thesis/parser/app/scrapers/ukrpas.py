from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from typing import Any, Optional, List

from thesis.parser.app.schemas import CitySchema, TicketData
from thesis.parser.app.scrapers.base import RequestScraper, _to_uah, logger


class UkrpasScraper(RequestScraper):
    """Scraper for ukrpas.ua (POST JSON API)."""

    @classmethod
    async def create(cls) -> "UkrpasScraper":
        return cls(await cls._load_site("ukrpas"))

    async def fetch(
        self,
        date: datetime,
        departure_city: CitySchema,
        arrival_city: CitySchema,
        **_: Any,
    ) -> Optional[List[dict]]:
        resp = await self._post(
            self.site.url,
            json={
                "fromId": departure_city.ukrpas_id,
                "toId": arrival_city.ukrpas_id,
                "dateTo": date.strftime("%Y-%m-%d"),
                "quantity": "1",
                "lng": "uk",
            },
            headers={
                "Content-Type": "text/plain;charset=UTF-8",
                "Accept": "application/json",
            },
        )
        return resp.json().get("trips") if resp else None

    def parse(
        self,
        content: List[dict],
        departure_city: CitySchema,
        arrival_city: CitySchema,
    ) -> List[TicketData]:
        tickets: List[TicketData] = []
        for trip in content:
            try:
                seg = trip.get("route", [{}])[0]
                points = seg.get("route", [])
                if len(points) < 2:
                    continue

                def _dt(s: str) -> Optional[datetime]:
                    try:
                        return datetime.strptime(s, "%Y-%m-%d %H:%M")
                    except Exception:
                        return None

                dep_dt = _dt(seg.get("departure_date_time", ""))
                arr_dt = _dt(seg.get("arrival_date_time", ""))
                from_pt = points[0].get("point", {})
                to_pt = points[-1].get("point", {})
                price_d = trip.get("price", {})
                raw_price = Decimal(price_d.get("total", 0)) / Decimal("100")
                price = raw_price.quantize(Decimal("0.01"), rounding=ROUND_DOWN)

                ticket = TicketData(
                    departure_datetime=dep_dt,  # type: ignore[arg-type]
                    arrival_datetime=arr_dt,
                    from_city_id=departure_city.id,
                    to_city_id=arrival_city.id,
                    from_station_name=(
                        f"{from_pt.get('name', '')} {from_pt.get('address', '')}".strip()
                    ),
                    to_station_name=(
                        f"{to_pt.get('name', '')} {to_pt.get('address', '')}".strip()
                    ),
                    carrier_name=seg.get("carrier", {}).get("name", "Unknown"),
                    travel_time=(arr_dt - dep_dt) if dep_dt and arr_dt else None,
                    price=price,
                    currency=price_d.get("currency", "Unknown"),
                    available_seats=trip.get("free_seats", 0),
                    is_transfer=bool(trip.get("trip_transfers")),
                )
                tickets.append(_to_uah(ticket, self.currencies))
            except Exception as exc:
                logger.error("UkrPas trip parse error: %s", exc)

        return tickets
