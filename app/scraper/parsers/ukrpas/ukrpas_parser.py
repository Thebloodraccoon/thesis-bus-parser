from datetime import datetime
from typing import List

from app.models import SiteModel
from app.scraper.schemas.city_schema import CitySchema
from app.scraper.schemas.ticket_schema import TicketDataSchema
from app.scraper.logger import get_logger
from app.scraper.parsers.base_parser import RequestParser
from app.scraper.parsers.ukrpas.ukrpas_helper import parse_trip_data
from app.scraper.parsers.utils import convert_ticket_to_uah


logger = get_logger(__name__)


class UkrpasParser(RequestParser):
    def __init__(self, site: SiteModel):
        super().__init__(site)

    @classmethod
    async def create(cls):
        site = await cls.load_site("ukrpas")
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
        url = f"{self.site.url}"
        body = {
            "fromId": departure_city.ukrpas_id,
            "toId": arrival_city.ukrpas_id,
            "dateTo": date.strftime("%Y-%m-%d"),
            "quantity": "1",
            "lng": "uk",
        }

        headers = {
            "Content-Type": "text/plain;charset=UTF-8",
            "Accept": "application/json",
        }
        try:
            response = await self.send_request(
                url, method="POST", json=body, headers=headers
            )
            if response:
                routes = response.json()
                return routes.get("trips", [])
            return None
        except Exception as e:
            logger.error(f"Error while retrieving routes: {e}")
            raise e

    def parse_data(
        self, content, departure_city: CitySchema, arrival_city: CitySchema
    ) -> List[TicketDataSchema]:
        parsed_data = []

        for trip in content:
            try:
                ticket = parse_trip_data(trip, departure_city.id, arrival_city.id)
                if ticket:
                    ticket = convert_ticket_to_uah(ticket, self.currencies)
                    parsed_data.append(ticket)
                else:
                    raise ValueError("Failed to parse trip data.")
            except Exception as e:
                logger.error(f"Error processing trip: {e}")
                raise e
        return parsed_data
