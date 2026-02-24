import asyncio
import difflib
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Union

from parser.app.managers.http import send_request
from parser.app.models import CityModel
from parser.app.settings.conf import get_db
from parser.app.settings.logger import get_logger

logger = get_logger(__name__)


def normalize_city_name(name):
    cleaned_name = re.sub(r"-", " ", name)
    cleaned_name = re.sub(r"[^\w\s]", "", cleaned_name).strip().lower()
    cleaned_name = cleaned_name.replace("ё", "e")
    cleaned_name = cleaned_name.replace("ґ", "г")
    if cleaned_name.endswith("ь") or cleaned_name.endswith("й"):
        cleaned_name = cleaned_name[:-1]
    sorted_words = cleaned_name.split()
    return " ".join(sorted_words)


def get_search_variants(
    city_name_ua: Optional[str], city_name_en: Optional[str] = None
) -> List[str]:
    normalize_name_ua = normalize_city_name(city_name_ua) if city_name_ua else None
    normalize_name_en = normalize_city_name(city_name_en) if city_name_en else None

    variants = [normalize_name_ua]

    if " " in normalize_name_ua:
        variants.append(normalize_name_ua.replace(" ", "-"))

    if normalize_name_en:
        variants.append(normalize_name_en)
        if " " in normalize_name_en:
            variants.append(normalize_name_en.replace(" ", "-"))

    return [v for v in variants if v]


def set_ids(
    city: CityModel,
    field_name: Union[str, List[str]],
    value: Any,
) -> bool:
    try:
        if isinstance(field_name, str):
            setattr(city, field_name, value)

        if isinstance(field_name, list) and isinstance(value, dict):
            for field in field_name:
                if field in value:
                    setattr(city, field, value[field])

        return True
    except Exception as e:
        logger.error(f"Error setting id for city {city.name_ua}: {e}")
        return False


class BaseCityParser(ABC):
    """Responsible for the logic of matching and working with the database."""

    def __init__(
        self,
        site_name: str,
        field_name: Union[str, List[str]],
        manual_map: Dict[str, Any] = None,
    ):
        self.site_name = site_name
        self.field_name = field_name
        self.manual_map = manual_map or {}
        self.scope_ratio = 0.85

    def _fuzzy_match(
        self,
        target_name: str,
        candidates: List[Dict[str, Any]],
        name_key: str,
        id_key: str,
    ) -> Optional[Any]:
        """
        Smart search. Not take the first one he comes across, but looks for the most similar one.
        candidates: a list of dictionaries that came from the API.
        """
        if not candidates:
            return None

        target_norm = target_name.lower()
        best_match = None
        highest_ratio = 0.0

        for item in candidates:
            api_name = str(item.get(name_key, "")).lower()
            if not api_name:
                continue

            if api_name == target_norm:
                return item.get(id_key)

            ratio = difflib.SequenceMatcher(None, target_norm, api_name).ratio()
            if ratio > highest_ratio:
                highest_ratio = ratio
                best_match = item

        if highest_ratio >= self.scope_ratio and best_match:
            logger.info(
                f"[{self.site_name}] Fuzzy match: '{target_name}' ~= '{best_match.get(name_key)}' (Score: {highest_ratio:.2f})"
            )
            return best_match.get(id_key)

        logger.debug(candidates)
        return None

    @abstractmethod
    async def run(self):
        """The startup method that the successor must implement."""
        pass

    def _filter_cities(self, cities: List[CityModel]) -> List[CityModel]:
        """
        Common method to filter out test cities and garbage data.
        """
        valid_cities = []
        for c in cities:
            name_ua = str(c.name_ua or "").lower()

            if "тест" in name_ua or "test" in name_ua:
                continue
            if "остановка на ланч" in name_ua:
                continue

            valid_cities.append(c)

        return valid_cities


class ApiCityParser(BaseCityParser):
    """
    For sites like Busfor, Kolobus.
    Searches for cities one by one via the API in multi-threaded mode.
    """

    def __init__(
        self,
        site_name: str,
        field_name: Union[str, List[str]],
        url: str,
        threads: int = 10,
        manual_map=None,
    ):
        super().__init__(site_name, field_name, manual_map)
        self.url = url
        self.semaphore = asyncio.Semaphore(threads)

    @abstractmethod
    def prepare_req_params(self, city_name: str) -> dict:
        """Return params or data to request requests."""
        pass

    @abstractmethod
    def parse_api_response(self, response_json: Any) -> List[Dict[str, Any]]:
        """
        Turns the API response into a list of dictionaries of the form: [{'name': '...', 'id': ...}, ...]
        IMPORTANT: Return ALL variants that the API has given, not just the first one.
        """
        pass

    async def _process_single_city(self, city_obj: CityModel) -> Tuple[CityModel, Any]:
        city_ua = str(city_obj.name_ua)

        if city_ua in self.manual_map:
            mapped_id = self.manual_map[city_ua]
            logger.info(
                f"[{self.site_name}] Found manual mapping for '{city_ua}': {mapped_id}"
            )
            return city_obj, mapped_id

        variants = get_search_variants(
            str(city_obj.name_ua), str(city_obj.name_en)
        )

        async with self.semaphore:
            for variant in variants:
                try:
                    params = self.prepare_req_params(variant)
                    resp = await send_request(url=self.url, **params)

                    if not resp or resp.status_code != 200:
                        logger.warning(
                            f"[{self.site_name}] Request failed or empty for variant '{variant}'"
                        )
                        continue

                    candidates = self.parse_api_response(resp.json())

                    found_id = self._fuzzy_match(
                        variant, candidates, name_key="name", id_key="id"
                    )

                    if found_id:
                        logger.success(
                            f"[{self.site_name}] Found city '{city_ua}' (variant: '{variant}') with ID {found_id}."
                        )
                        return city_obj, found_id

                    logger.warning(
                        f"[{self.site_name}] City '{variant}' not found (API returned {len(candidates)} candidates)."
                    )

                except Exception as e:
                    logger.error(f"[{self.site_name}] Error checking '{variant}': {e}")

        logger.error(
            f"[{self.site_name}] City '{city_ua}' not found in any search variants {variants}."
        )
        return city_obj, None

    async def run(self):
        logger.info(f"[{self.site_name}] Starting Parallel Update...")

        with get_db() as s:
            all_cities = s.query(CityModel).all()
            s.expunge_all()

        cities = self._filter_cities(all_cities)
        logger.info(
            f"[{self.site_name}] Processing {len(cities)} cities (filtered {len(all_cities) - len(cities)} items)."
        )

        tasks = [self._process_single_city(c) for c in cities]
        results = await asyncio.gather(*tasks)

        cnt = 0
        with get_db() as s:
            for city_obj, new_id in results:
                if new_id:
                    merged_city = s.merge(city_obj)
                    if set_ids(merged_city, self.field_name, new_id):
                        s.add(merged_city)
                        cnt += 1
            s.commit()
        logger.success(f"[{self.site_name}] Updated {cnt} cities.")


class BulkCityParser(BaseCityParser):
    """For sites like VisitTour.
    Downloads 1 large JSON and matches locally."""

    @abstractmethod
    async def fetch_all_data(self) -> List[Dict[str, Any]]:
        """Should return a list of cities: [{'name': '...', 'id': ...}]"""
        pass

    async def run(self):
        logger.info(f"[{self.site_name}] Starting Bulk Update...")

        try:
            api_data = await self.fetch_all_data()
            if not api_data:
                logger.error(f"[{self.site_name}] No data received.")
                return
        except Exception as e:
            logger.error(f"[{self.site_name}] Failed to fetch data: {e}")
            return

        logger.info(
            f"[{self.site_name}] Loaded {len(api_data)} items from API. Starting matching..."
        )

        cnt = 0
        with get_db() as s:
            all_cities = s.query(CityModel).all()
            cities = self._filter_cities(all_cities)

            logger.info(
                f"[{self.site_name}] Processing {len(cities)} cities (filtered {len(all_cities) - len(cities)} items)."
            )

            for city in cities:
                city_ua = str(city.name_ua)

                if city_ua in self.manual_map:
                    mapped_id = self.manual_map[city_ua]
                    logger.info(
                        f"[{self.site_name}] Found manual mapping for '{city_ua}': {mapped_id}"
                    )
                    if set_ids(city, self.field_name, mapped_id):
                        s.add(city)
                        cnt += 1
                    continue

                variants = get_search_variants(
                    str(city.name_ua), str(city.name_en)
                )
                found_id = None
                used_variant = None

                for variant in variants:
                    found_id = self._fuzzy_match(
                        variant, api_data, name_key="name", id_key="id"
                    )
                    if found_id:
                        used_variant = variant
                        break

                if found_id:
                    logger.success(
                        f"[{self.site_name}] Found city '{city_ua}' (variant: '{used_variant}') with ID {found_id}."
                    )
                    if set_ids(city, self.field_name, found_id):
                        s.add(city)
                        cnt += 1
                else:
                    logger.error(
                        f"[{self.site_name}] City '{city_ua}' not found in bulk data. Checked variants: {variants}"
                    )

            s.commit()
        logger.success(f"[{self.site_name}] Updated {cnt} cities.")
