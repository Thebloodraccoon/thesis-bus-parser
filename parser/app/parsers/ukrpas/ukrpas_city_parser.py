from typing import Any, List, Dict

from parser.app.managers.parser.parser_city_manager import ApiCityParser

API_URL = "https://ukrpas.ua/api/locations"
BASE_PARAMS = {"lng": "ru"}
MANUAL_MAPPING_IDS = {
    "Могилёв": 1573363,
    "Долгобичув": 1609731,
    "Пётркув-Трыбунальский": 1172929,
    "Аэропорт Яссы": 1576669,
    "Переяслав-Хмельницкий": 1114159,
    "Кёльн Аэропорт": 1582033,
}


class UkrPasCityParser(ApiCityParser):
    def __init__(self):
        super().__init__(
            site_name="UkrPas",
            field_name="ukrpas_id",
            url=API_URL,
            threads=10,
            manual_map=MANUAL_MAPPING_IDS,
        )

    def prepare_req_params(self, city_name: str) -> dict:
        """
        UkrPas uses GET request with 'query' parameter and 'lng=ru'.
        """
        params = BASE_PARAMS.copy()
        params["query"] = city_name

        return {"method": "GET", "params": params}

    def parse_api_response(self, response_json: Any) -> List[Dict[str, Any]]:
        """
        Parses UkrPas response.
        Expected format: [{"id": 123, "name": "CityName", ...}, ...]
        """
        if not response_json or not isinstance(response_json, list):
            return []

        candidates = []
        for item in response_json:
            city_id = item.get("id")
            raw_name = item.get("name")

            if city_id and raw_name:
                candidates.append(
                    {
                        "name": raw_name,
                        "id": int(city_id),
                    }
                )

        return candidates
