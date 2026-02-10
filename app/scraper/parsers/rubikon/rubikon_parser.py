from datetime import datetime
from typing import List

from app.models import SiteModel
from app.scraper.parsers.base_parser import RequestParser
from app.scraper.parsers.utils import convert_ticket_to_uah
from app.scraper.schemas.city_schema import CitySchema
from app.scraper.schemas.ticket_schema import TicketDataSchema
from app.scraper.parsers.rubikon.rubikon_helper import get_all_tickets, parse_trip_data
from app.scraper.logger import get_logger

logger = get_logger(__name__)


class RubikonParser(RequestParser):
    def __init__(self, site: SiteModel):
        super().__init__(site)


    @classmethod
    async def create(cls):
        site = await cls.load_site("rubikon")
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
        url = f"{self.site.url}/departures"
        try:
            params = {
                "departureDate": date.strftime("%Y-%m-%d"),
                "passengers[adults][count]": 1,
                "currencyId": 18,
                "from[id]": departure_city.rubikon_id,
                "to[id]": arrival_city.rubikon_id,
            }
            headers = {
                "authorization": "",
                "cache-control": "no-cache",
                "lang": "uk",
            }

            result, response_size_kb = await get_all_tickets(
                url=url, params=params, headers=headers
            )
            self.update_response_stats(response_size_kb)

            return result
        except Exception as e:
            logger.error(f"Error parsing routes: {e}")
            raise e

    def parse_data(
        self, content, departure_city: CitySchema, arrival_city: CitySchema
    ) -> List[TicketDataSchema]:
        parsed_data = []
        for trip in content:
            try:
                ticket = parse_trip_data(
                    trip,
                    departure_city.id,
                    arrival_city.id,
                )
                if ticket:
                    ticket = convert_ticket_to_uah(ticket, self.currencies)
                    parsed_data.append(ticket)
                else:
                    raise ValueError("Failed to parse trip data.")
            except Exception as e:
                logger.error(f"Error processing trip: {e}")
                raise e
        return parsed_data
