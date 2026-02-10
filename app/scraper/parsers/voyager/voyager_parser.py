from datetime import datetime
from typing import List

from app.models import SiteModel
from app.scraper.schemas.city_schema import CitySchema
from app.scraper.schemas.ticket_schema import TicketDataSchema
from app.scraper.logger import get_logger
from app.scraper.parsers.base_parser import RequestParser
from app.scraper.parsers.utils import convert_ticket_to_uah
from app.scraper.parsers.voyager.voyager_helper import parse_trip_data

logger = get_logger(__name__)


class VoyagerParser(RequestParser):
    def __init__(self, site: SiteModel):
        super().__init__(site)

    @classmethod
    async def create(cls):
        site = await cls.load_site("voyager")
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
        url = f"{self.site.url}/Courses/CoursesList"
        try:
            json = {
                "form": {
                    "adults": 1,
                    "departure": True,
                    "cityFrom": {"code": departure_city.voyager_id},
                    "cityTo": {"code": arrival_city.voyager_id},
                    "date": date.strftime("%Y-%m-%d"),
                    "agent": "VOYAGER0KK",
                    "currency": "PLN",
                }
            }

            response = await self.send_request(
                url=url,
                method="POST",
                json=json,
            )

            if response and response.status_code == 200:
                return response.json()["coursesList"]
            return None
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
