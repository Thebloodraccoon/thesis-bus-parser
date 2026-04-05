from __future__ import annotations

import asyncio
import difflib
import json
import random
import re
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx

from thesis.core.models import CityModel
from thesis.parser.app.schemas import CityCreate, CitySchema, CurrencySchema, RouteData
from thesis.parser.app.repository import (
    CityRepository,
    CurrencyRepository,
    db_session,
)
from thesis.parser.app.scrapers.base import get_async_client
from thesis.parser.app.settings.config import settings
from thesis.parser.app.settings.logger import get_logger

logger = get_logger(__name__)


def _normalize(name: str) -> str:
    name = re.sub(r"-", " ", name)
    name = re.sub(r"[^\w\s]", "", name).strip().lower()
    name = name.replace("ё", "e").replace("ґ", "г")
    if name.endswith(("ь", "й")):
        name = name[:-1]

    return " ".join(name.split())


def _variants(name_ua: Optional[str], name_en: Optional[str] = None) -> List[str]:
    results: List[str] = []
    for raw in (name_ua, name_en):
        if not raw:
            continue

        norm = _normalize(raw)
        results.append(norm)
        if " " in norm:
            results.append(norm.replace(" ", "-"))

    return [v for v in results if v]


# Base city matcher
class CityMatcher(ABC):
    """Abstract base for all city-matching strategies."""

    FUZZY_THRESHOLD = 0.85

    def __init__(
        self,
        site_name: str,
        field_name: str,
        manual_map: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.site_name = site_name
        self.field_name = field_name
        self.manual_map = manual_map or {}

    @abstractmethod
    async def run(self) -> None:
        """Resolve and persist city IDs for *all* cities in the DB."""

    def _fuzzy_match(
            self,
            target: str,
            candidates: List[Dict[str, Any]],
            name_key: str = "name",
            id_key: str = "id",
    ) -> Optional[Any]:
        target_norm = target.lower()
        best_id, best_ratio, best_name = None, 0.0, None

        for item in candidates:
            api_name = str(item.get(name_key, "")).lower()

            if api_name == target_norm:
                return item.get(id_key)

            ratio = difflib.SequenceMatcher(None, target_norm, api_name).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_id = item.get(id_key)
                best_name = item.get(name_key)

        if best_ratio >= self.FUZZY_THRESHOLD and best_id is not None:
            logger.info(
                f"[{self.site_name}] Fuzzy match score={best_ratio:.2f} | target='{target}' -> matched API name='{best_name}'"
            )
            return best_id

        return None

    @staticmethod
    def _filter(cities: List[CityModel]) -> List[CityModel]:
        return [
            c
            for c in cities
            if "тест" not in (c.name_ua or "").lower()
            and "test" not in (c.name_ua or "").lower()
            and "обід" not in (c.name_ua or "").lower()
        ]

    def _apply(self, city_id: int, value: Any, session) -> bool:
        return CityRepository(session).set_site_city_id(city_id, self.field_name, value)


# Bulk city matcher
class BulkCityMatcher(CityMatcher, ABC):
    """Downloads a single large JSON and matches all cities locally."""

    @abstractmethod
    async def _fetch_all(self) -> List[Dict[str, Any]]:
        """Return list of ``{"name": ..., "id": ...}`` from the remote API."""

    async def run(self) -> None:
        api_data = await self._fetch_all()
        if not api_data:
            logger.error(f"{self.site_name} No data received from API")
            return

        cnt = 0
        with db_session() as s:
            cities = self._filter(s.query(CityModel).all())
            for city in cities:
                name_ua = str(city.name_ua)

                if name_ua in self.manual_map:
                    if self._apply(city.id, self.manual_map[name_ua], s):
                        cnt += 1
                    continue

                found_id = None
                for variant in _variants(city.name_ua, city.name_en):
                    found_id = self._fuzzy_match(variant, api_data)
                    if found_id:
                        break

                if found_id and self._apply(city.id, found_id, s):
                    cnt += 1
            s.commit()

        logger.info(f"[{self.site_name}] Updated {cnt} cities")


class InbusCityMatcher(BulkCityMatcher):
    _API_URL = "https://inbus.in.ua/api/v2/points/"
    _API_PARAMS = {"lang": "uk"}
    _MANUAL: Dict[str, Any] = {
        "Долгобичув": 9616043851,
        "Кёльн Аэропорт": 9276028724,
        "Переяслав-Хмельницкий": 9804000591,
    }

    def __init__(self) -> None:
        super().__init__("Inbus", "inbus_id", self._MANUAL)

    async def _fetch_all(self) -> List[Dict[str, Any]]:
        async with get_async_client() as client:
            home = await client.get("https://inbus.ua/")
            cookies = dict(home.cookies)
            token = None
            raw = cookies.get("userData")
            if raw:
                try:
                    token = json.loads(raw).get("access_token")
                except Exception as e:
                    logger.error(f"{self.site_name} Failed to parse access_token: {e}")
                    pass

            headers = {"x-api-access-token": token or ""}
            resp = await client.get(
                self._API_URL, params=self._API_PARAMS, cookies=cookies, headers=headers
            )
        return [
            {"name": c["name"], "id": c["id"]}
            for c in resp.json().get("points", {}).get("cities", [])
            if c.get("name") and c.get("id")
        ]


class VoyagerCityMatcher(BulkCityMatcher):
    _API_URL = (
        "https://partners.voyager.pl/assets/dictionary/"
        "CityPARTNER000/CityDictionary-pl.json"
    )
    _MANUAL: Dict[str, int] = {"Кёльн Аэропорт": 643, "Звягель": 102807}

    def __init__(self) -> None:
        super().__init__("Voyager", "voyager_id", self._MANUAL)

    async def _fetch_all(self) -> List[Dict[str, Any]]:
        async with get_async_client() as client:
            resp = await client.get(self._API_URL)
        return [
            {"name": item["city"], "id": int(item["nr"])}
            for item in resp.json()
            if item.get("city") and item.get("nr")
        ]


# API city matcher
class ApiCityMatcher(CityMatcher, ABC):
    """Queries the remote API individually for each city (concurrent)."""

    def __init__(
        self,
        site_name: str,
        field_name: str,
        api_url: str,
        threads: int = 10,
        manual_map: Optional[Dict] = None,
    ) -> None:
        super().__init__(site_name, field_name, manual_map)
        self._api_url = api_url
        self._semaphore = asyncio.Semaphore(threads)

    @abstractmethod
    def _build_params(self, city_name: str) -> dict:
        """Return kwargs for a httpx GET request (params, headers, …)."""

    @abstractmethod
    def _parse_response(self, response_json: Any) -> List[Dict[str, Any]]:
        """Return ``[{"name": ..., "id": ...}, …]`` from the raw API JSON."""

    async def _resolve_city(self, city: CityModel) -> Tuple[CityModel, Optional[Any]]:
        name_ua = str(city.name_ua)
        if name_ua in self.manual_map:
            return city, self.manual_map[name_ua]

        async with self._semaphore:
            for variant in _variants(city.name_ua, city.name_en):
                try:
                    kwargs = self._build_params(variant)
                    async with get_async_client() as client:
                        resp = await client.get(self._api_url, **kwargs)

                    candidates = self._parse_response(resp.json())
                    found = self._fuzzy_match(variant, candidates)
                    if found:
                        return city, found

                except Exception as exc:
                    logger.error(
                        f"[{self.site_name}] Error for '{variant}': {exc}"
                    )

        return city, None

    async def run(self) -> None:
        with db_session() as s:
            all_cities = s.query(CityModel).all()
            s.expunge_all()

        cities = self._filter(all_cities)
        results = await asyncio.gather(*[self._resolve_city(c) for c in cities])

        cnt = 0
        with db_session() as s:
            for city, new_id in results:
                if new_id:
                    merged = s.merge(city)
                    setattr(merged, self.field_name, new_id)
                    s.add(merged)
                    cnt += 1
            s.commit()

        logger.info(f"[{self.site_name}] Updated {cnt} cities.")


class UkrpasCityMatcher(ApiCityMatcher):
    _MANUAL: Dict[str, int] = {
        "Переяслав-Хмельницкий": 1114159,
        "Кёльн Аэропорт": 1582033,
        "Аэропорт Яссы": 1576669,
    }

    def __init__(self) -> None:
        super().__init__(
            "UkrPas",
            "ukrpas_id",
            "https://ukrpas.ua/api/locations",
            threads=10,
            manual_map=self._MANUAL,
        )

    def _build_params(self, city_name: str) -> dict:
        return {"params": {"lng": "ru", "query": city_name}}

    def _parse_response(self, data: Any) -> List[Dict[str, Any]]:
        if not isinstance(data, list):
            return []
        return [
            {"name": i["name"], "id": int(i["id"])}
            for i in data
            if i.get("id") and i.get("name")
        ]


class RubikonCityMatcher(ApiCityMatcher):
    _MANUAL: Dict[str, int] = {
        "Хмельницкий": 2955,
        "Киев": 1835,
        "Одесса": 2367,
        "Тернополь": 2867,
        "Винница": 1496,
        "Вена": 1,
        "Берлин": 179,
        "Кёльн": 213,
    }

    def __init__(self) -> None:
        super().__init__(
            "Rubikon",
            "rubikon_id",
            "https://api.rubikon.com.ua/api/v1/locations",
            threads=10,
            manual_map=self._MANUAL,
        )

    def _build_params(self, city_name: str) -> dict:
        return {
            "params": {"search": city_name},
            "headers": {"lang": "ru", "Accept": "application/json"},
        }

    def _parse_response(self, data: Any) -> List[Dict[str, Any]]:
        items = data.get("data", {}).get("data", []) if isinstance(data, dict) else []
        return [
            {"name": i["name"]["uk"], "id": int(i["id"])}
            for i in items
            if i.get("id") and isinstance(i.get("name"), dict) and i["name"].get("uk")
        ]


# Currency service
class CurrencyService:
    """Fetches and persists exchange rates from the NBU API."""

    _NBU_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange"
    _BYN_URL = "https://minfin.com.ua/api/coin/graph/byn/uah"

    async def refresh(self) -> List[Dict[str, Any]]:
        logger.info("Starting currency exchange rates refresh from APIs...")

        async with httpx.AsyncClient(follow_redirects=True) as client:
            nbu_data = []
            try:
                logger.debug(f"Fetching NBU rates from {self._NBU_URL}")
                nbu_resp = await client.get(self._NBU_URL, params={"json": ""})
                nbu_resp.raise_for_status()
                nbu_data = nbu_resp.json()
                logger.info(f"Successfully fetched {len(nbu_data)} rates from NBU.")
            except Exception as exc:
                logger.error(f"Failed to fetch NBU rates: {exc}")

            byn_rate: Optional[float] = None
            try:
                today = date.today().isoformat()
                logger.debug(f"Fetching BYN rate from {self._BYN_URL}")
                byn_resp = await client.get(f"{self._BYN_URL}/{today}/{today}/days/")
                byn_resp.raise_for_status()
                byn_data = byn_resp.json()

                raw = (
                    (byn_data.get("data") or [{}])[-1]
                    .get("course", {})
                    .get("banks", {})
                    .get("bid")
                )
                byn_rate = float(raw) if raw and raw != "-" else None

                if byn_rate:
                    logger.info(f"Successfully fetched BYN rate: {byn_rate}")
                else:
                    logger.warning("BYN rate fetch returned empty or invalid value.")

            except Exception as exc:
                logger.warning(f"BYN rate fetch failed: {exc}")

        updated: List[Dict[str, Any]] = []
        if not nbu_data and not byn_rate:
            logger.warning("No currency data was fetched. Skipping database update.")
            return updated

        logger.debug("Starting to persist currency records to DB...")
        with db_session() as s:
            repo = CurrencyRepository(s)
            for item in nbu_data:
                result = self._persist(
                    repo, item.get("cc"), item.get("rate"), item.get("exchangedate")
                )
                if result:
                    updated.append(result)

            if byn_rate:
                result = self._persist(repo, "BYN", byn_rate, None)
                if result:
                    updated.append(result)

        logger.info(f"Currency refresh completed. Updated {len(updated)} currency records in DB.")
        return updated

    @staticmethod
    def _persist(
            repo: CurrencyRepository,
            code: Optional[str],
            rate: Any,
            date_str: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        if not code or not rate:
            logger.debug(f"Skipping persistence: missing code or rate (code: {code}, rate: {rate}).")
            return None
        try:
            ex_date = date.today()
            if date_str:
                d, m, y = date_str.split(".")
                ex_date = date(int(y), int(m), int(d))

            obj = repo.update_or_create(
                CurrencySchema(code=code, rate=float(rate), exchange_date=ex_date)
            )
            logger.debug(f"Persisted: {code} -> {rate} (date: {ex_date})")
            return {"code": obj.code, "rate": obj.rate, "date": str(obj.exchange_date)}
        except Exception as exc:
            logger.error(f"Currency persist error ({code}): {exc}")
            return None


# Route fetcher (LikeBus partner API)
class RouteFetcher:
    """
    Retrieves the list of routes to be scraped for a given date from
    the LikeBus partner API and resolves city objects from the local DB.
    """

    _ROUTES_URL = "https://likebus.ua/sync/v3/routes/dayInfoTesting"
    _CITIES_URL = "https://likebus.ua/sync/v3/catalog/city"

    @classmethod
    def sync_cities(cls) -> List[dict]:
        """Download city catalogue and upsert into the DB."""

        resp = httpx.get(cls._CITIES_URL, follow_redirects=True)
        data = resp.json()
        with db_session() as s:
            repo = CityRepository(s)
            repo.fix_sequence()

            for item in data:
                try:
                    name_ua = item.get("loc", {}).get("ua", {}).get("name", "")
                    name_en = item.get("loc", {}).get("en", {}).get("name", "")
                    if not name_ua.strip() and not name_en.strip():
                        continue

                    repo.update_or_create(
                        CityCreate(
                            like_bus_id=int(item["id"]),
                            name_ua=name_ua,
                            name_en=name_en,
                        )
                    )

                except Exception as exc:
                    logger.error(f"City upsert error: {exc}")
            s.commit()
        return data

    @classmethod
    def get_routes(cls, for_date: datetime) -> List["RouteData"]:  # noqa: F821
        """Fetch routes from the partner API and resolve city schemas."""

        date_str = for_date.strftime("%Y-%m-%d")
        resp = httpx.get(
            cls._ROUTES_URL,
            headers={"X-API-KEY": settings.API_KEY},
            params={"date": date_str},
            timeout=30,
        )
        raw_routes = resp.json().get("list", [])
        result: List[RouteData] = []

        with db_session() as s:
            city_repo = CityRepository(s)
            for route in raw_routes:
                dep = city_repo.get_by_like_bus_id(route["departure_city_id"])
                arr = city_repo.get_by_like_bus_id(route["arrival_city_id"])
                if not dep or not arr:
                    continue

                try:
                    result.append(
                        RouteData(
                            departure_city=CitySchema.model_validate(dep),
                            arrival_city=CitySchema.model_validate(arr),
                            route_id=route["route_id"],
                            trip_id=str(route["trip_id"]),
                            from_date=datetime.strptime(
                                str(route["departure_time"]).strip()[:19],
                                "%Y-%m-%d %H:%M:%S",
                            ),
                            to_date=datetime.strptime(
                                str(route["arrival_time"]).strip()[:19],
                                "%Y-%m-%d %H:%M:%S",
                            ),
                            departure_station_id=route.get("departure_station_id"),
                            arrival_station_id=route.get("arrival_station_id"),
                        )
                    )
                except Exception as exc:
                    logger.error(f"Route data build error: {exc}")

        random.shuffle(result)
        return result
