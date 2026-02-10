from typing import List, Dict, Any

from app.scraper.managers.parser.parser_city_manager import BulkCityParser
from app.scraper.managers.http import send_request

API_URL = "https://partners.voyager.pl/assets/dictionary/CityPARTNER000/CityDictionary-pl.json"

MANUAL_MAPPING_IDS = {
    "Кёльн Аэропорт": 643,
    "Звягель": 102807,
}


class VoyagerCityParser(BulkCityParser):
    def __init__(self):
        super().__init__(
            site_name="Voyager", field_name="voyager_id", manual_map=MANUAL_MAPPING_IDS
        )

    async def fetch_all_data(self) -> List[Dict[str, Any]]:
        """
        Downloads the full city dictionary from Voyager.
        Expected format: [{"nr": 123, "city": "Name", ...}, ...]
        """
        response = await send_request(url=API_URL, method="GET", follow_redirects=True)

        if not response or response.status_code != 200:
            return []

        data = response.json()

        if not isinstance(data, list):
            return []

        candidates = []
        for item in data:
            city_id = item.get("nr")
            raw_name = item.get("city")

            if city_id and raw_name:
                candidates.append(
                    {"name": raw_name, "id": int(city_id), "original_name": raw_name}
                )

        return candidates
