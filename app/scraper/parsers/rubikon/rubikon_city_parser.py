from typing import Any, List, Dict

from app.scraper.managers.parser.parser_city_manager import ApiCityParser


API_URL = "https://api.rubikon.com.ua/api/v1/locations"
HEADERS = {
    "lang": "ru",
    "Accept": "application/json",
}
MANUAL_MAPPING_IDS = {
    "Аэропорт Яссы": 944,
    "Хмельницкий": 2955,
    "Переяслав-Хмельницкий": 2458,
    "Вроцлав": 553,
    "Днепр": 1648,
    "Одесса": 2367,
    "Киев": 1835,
    "Умань": 2924,
    "Катерини": 314,
    "Лодзь": 671,
    "Звягель": 2326,
    "Пётркув-Трыбунальский": 752,
    "Хелм": 873,
    "Вена": 1,
    "Берлин": 179,
    "Линц": 3,
    "Тернополь": 2867,
    "Жешув": 598,
    "Торунь": 856,
    "Кёльн": 213,
    "Мамая": 922,
    "Зосин": 613,
    "Благовещенское": 1234,
    "Брэила": 910,
    "Батуми": 311,
    "Винница": 1496,
    "Южноукраинск": 3090,
    "Лубны": 2067,
    "Пшеворск": 751,
    "Славянск": 2735,
    "Малко-Тырново": 29,
    "Кёльн Аэропорт": 213,
    "Каменка": 5608,
    "Яремче": 3111,
}


class RubikonCityParser(ApiCityParser):
    def __init__(self):
        super().__init__(
            site_name="Rubikon",
            field_name="rubikon_id",
            url=API_URL,
            threads=10,
            manual_map=MANUAL_MAPPING_IDS,
        )

    def prepare_req_params(self, city_name: str) -> dict:
        """
        Rubikon uses GET param 'search' and requires 'lang' header.
        """
        return {"method": "GET", "params": {"search": city_name}, "headers": HEADERS}

    def parse_api_response(self, response_json: Any) -> List[Dict[str, Any]]:
        """
        Parses Rubikon response.
        Structure: {"data": {"data": [{"id": ..., "name": ...}, ...]}}
        """
        if not response_json or not isinstance(response_json, dict):
            return []

        data_wrapper = response_json.get("data", {})
        if not isinstance(data_wrapper, dict):
            return []

        items = data_wrapper.get("data", [])
        if not isinstance(items, list):
            return []

        candidates = []
        for item in items:
            city_id = item.get("id")
            raw_name = item.get("name").get("uk")

            if city_id and raw_name:
                candidates.append(
                    {
                        "name": raw_name,
                        "id": int(city_id),
                    }
                )

        return candidates
