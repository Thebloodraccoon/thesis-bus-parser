from datetime import datetime
from typing import List

from app.core.models import SiteModel
from app.parser.parsers.base_parser import RequestParser
from app.parser.parsers.inbus.inbus_helper import get_cookies, get_request_url, parse_trip_data
from app.parser.parsers.utils import convert_ticket_to_uah
from app.parser.schemas.city_schema import CitySchema
from app.parser.schemas.ticket_schema import TicketDataSchema
from app.parser.settings.logger import get_logger

logger = get_logger(__name__)


class InbusParser(RequestParser):
    def __init__(self, site: SiteModel):
        super().__init__(site)
        self.cookies = None

    async def init_async(self):
        self.cookies, response_size = await get_cookies("https://inbus.ua/")
        self.update_response_stats(response_size)

    @classmethod
    async def create(cls):
        site = await cls.load_site("inbus")
        instance = cls(site)
        await instance.init_async()
        return instance

    async def get_content(
        self,
        date: datetime,
        departure_city: CitySchema,
        arrival_city: CitySchema,
        **kwargs,
    ):
        url_token, response_size = await get_request_url()
        self.update_response_stats(response_size)

        url = f"{self.site.url}{url_token}/uk/search.json"
        params = {
            "date_from": date.strftime("%Y-%m-%d"),
            "from_id": str(departure_city.inbus_id),
            "to_id": str(arrival_city.inbus_id),
        }
        try:
            response = await self.send_request(
                url=url, method="GET", params=params, cookies=self.cookies, timeout=180
            )
            if response:
                json_response = response.json()
                if json_response.get("pageProps").get("route").get("variants"):
                    routes = json_response.get("pageProps").get("route").get("variants")
                    return routes
                return None
            return None

        except Exception as e:
            logger.error(f"Error parsing routes: {e}")
            raise e

    def parse_data(
        self, content, departure_city: CitySchema, arrival_city: CitySchema
    ) -> List[TicketDataSchema]:
        parsed_data = []
        for route in content:
            for trip in route.get("segments"):
                try:
                    ticket = parse_trip_data(trip, departure_city, arrival_city)
                    if ticket:
                        ticket = convert_ticket_to_uah(ticket, self.currencies)
                        parsed_data.append(ticket)
                    else:
                        raise ValueError("Failed to parse trip data.")
                except Exception as e:
                    logger.error(f"Error processing trip: {e}")
                    raise e
        return parsed_data
