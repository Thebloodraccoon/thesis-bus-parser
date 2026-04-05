from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Any, List

from bs4 import BeautifulSoup

from thesis.core.models import SiteModel
from thesis.parser.app.settings.logger import get_logger
from thesis.parser.app.schemas import CitySchema, TicketData
from thesis.parser.app.scrapers.base import RequestScraper, _to_uah

logger = get_logger(__name__)


class InbusScraper(RequestScraper):
    """Scraper for inbus.ua."""

    _API_URL = "https://inbus.in.ua/api/v2/points/"
    _API_PARAMS = {"lang": "uk"}

    def __init__(self, site: SiteModel) -> None:
        super().__init__(site)
        self._cookies: Optional[dict] = None

    @classmethod
    async def create(cls) -> "InbusScraper":
        site = await cls._load_site("inbus")
        instance = cls(site)
        await instance._init_cookies()
        return instance

    async def _init_cookies(self) -> None:
        resp = await self._get("https://inbus.ua/")
        self._cookies = dict(resp.cookies)

    def _extract_token(self) -> Optional[str]:
        if not self._cookies:
            return None
        import json

        raw = self._cookies.get("userData")
        if raw:
            try:
                return json.loads(raw).get("access_token")
            except Exception:
                pass
        return None

    async def fetch(
            self,
            date: datetime,
            departure_city: CitySchema,
            arrival_city: CitySchema,
            **_: Any,
    ) -> Optional[List[dict]]:
        site_resp = await self._get("https://inbus.ua/")
        soup = BeautifulSoup(site_resp.text, "html.parser")
        url_token = next(
            (
                s["src"].split("/_next/static/")[1].split("/_buildManifest.js")[0]
                for s in soup.find_all("script", src=True)
                if "/_next/static/" in s["src"] and "_buildManifest.js" in s["src"]
            ),
            None,
        )

        if not url_token:
            raise ValueError("Inbus build token not found.")

        url = f"{self.site.url}{url_token}/uk/search.json"
        resp = await self._get(
            url,
            params={
                "date_from": date.strftime("%Y-%m-%d"),
                "from_id": str(departure_city.inbus_id),
                "to_id": str(arrival_city.inbus_id),
            },
            cookies=self._cookies,
            headers={"x-api-access-token": self._extract_token() or ""},
            timeout=180,
        )

        data = resp.json()

        page_props = data.get("pageProps")
        if not isinstance(page_props, dict):
            return None

        route_data = page_props.get("route")
        if not isinstance(route_data, dict):
            return None

        variants = route_data.get("variants")
        if isinstance(variants, dict):
            variants = list(variants.values())

        return variants if isinstance(variants, list) else None

    def parse(
            self,
            content: Any,
            departure_city: CitySchema,
            arrival_city: CitySchema,
    ) -> List[TicketData]:
        tickets: List[TicketData] = []

        if not isinstance(content, list):
            return tickets

        for route in content:
            if not isinstance(route, dict):
                continue

            segments = route.get("segments")
            if isinstance(segments, dict):
                segments = list(segments.values())

            if not isinstance(segments, list):
                continue

            for segment in segments:
                if not isinstance(segment, dict):
                    continue

                ticket = self._parse_segment(segment, departure_city, arrival_city)
                if ticket:
                    tickets.append(_to_uah(ticket, self.currencies))

        return tickets

    @staticmethod
    def _parse_segment(
        seg: dict, dep: CitySchema, arr: CitySchema
    ) -> Optional[TicketData]:
        try:
            dep_dt = datetime.strptime(seg["departure"], "%Y-%m-%d %H:%M")
            arr_dt = datetime.strptime(seg["arrival"], "%Y-%m-%d %H:%M")
            price_raw = seg.get("cost", {}).get("min")
            if price_raw is None:
                return None

            return TicketData(
                departure_datetime=dep_dt,
                arrival_datetime=arr_dt,
                from_city_id=dep.id,
                to_city_id=arr.id,
                from_station_name=dep.name_ua,
                to_station_name=arr.name_ua,
                carrier_name=seg.get("transporter", {}).get("name", ""),
                travel_time=arr_dt - dep_dt,
                price=Decimal(str(price_raw)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                ),
                currency=seg.get("cost", {}).get("currency", {}).get("alpha3", ""),
                available_seats=seg.get("free_seats", 0),
                is_transfer=bool(seg.get("transit", False)),
            )

        except Exception as exc:
            logger.error("Inbus segment parse error: %s", exc)
            return None
