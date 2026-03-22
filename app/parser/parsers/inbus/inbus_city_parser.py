import json
from typing import Any, List, Dict

from app.parser.managers.http import send_request
from app.parser.managers.parser.parser_city_manager import BulkCityParser
from app.parser.parsers.inbus.inbus_helper import get_cookies

API_URL = "https://inbus.in.ua/api/v2/points/"
API_PARAMS = {"lang": "uk"}


def get_access_token(cookies) -> Any | None:
    try:
        cookies_dict = cookies.jar._cookies
        for domain in cookies_dict:
            for path in cookies_dict[domain]:
                for name, cookie in cookies_dict[domain][path].items():
                    if name == "userData":
                        user_data = json.loads(cookie.value)
                        return user_data.get("access_token")
    except Exception as e:
        print(f"Error extracting access token: {e}")
    return None


async def get_inbus_data():
    cookies, _ = await get_cookies("https://inbus.ua/")
    headers = {"x-api-access-token": get_access_token(cookies)}
    city_data = await send_request(
        "https://inbus.in.ua/api/v2/points/",
        method="GET",
        cookies=cookies,
        params=API_PARAMS,
        headers=headers,
    )

    return city_data.json().get("points", "").get("cities", "")


MANUAL_CITY_ID_MAPPING = {
    "Долгобичув": 9616043851,
    "Кёльн Аэропорт": 9276028724,
    "Брэила": 9642002831,
    "Свети Влас": 9100000309,
    "Мамая": 9642011960,
    "Аэропорт Яссы": 9642011958,
    "Тчев": 9616033501,
    "Красноград": 9804014944,
    "Золочев": 9804010850,
    "Переяслав-Хмельницкий": 9804000591,
}


class InbusCityParser(BulkCityParser):
    def __init__(self):
        super().__init__(
            site_name="Inbus", field_name="inbus_id", manual_map=MANUAL_CITY_ID_MAPPING
        )

    async def fetch_all_data(self) -> List[Dict[str, Any]]:
        cookies, _ = await get_cookies("https://inbus.ua/")

        token = get_access_token(cookies)
        headers = {"x-api-access-token": token} if token else {}

        response = await send_request(
            API_URL,
            method="GET",
            cookies=cookies,
            params=API_PARAMS,
            headers=headers,
        )

        if not response:
            return []

        data = response.json()

        cities_list = data.get("points", {}).get("cities", [])

        candidates = []
        for item in cities_list:
            if item.get("name") and item.get("id"):
                candidates.append({"name": item.get("name"), "id": item.get("id")})

        return candidates
