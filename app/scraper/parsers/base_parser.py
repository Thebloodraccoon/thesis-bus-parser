from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List

from pydantic import ValidationError

from app.models import SiteModel
from app.scraper.schemas.city_schema import CitySchema
from app.scraper.schemas.route_schema import RouteSchema
from app.scraper.schemas.ticket_schema import TicketDataSchema
from app.scraper.schemas.trip_history_schema import TripHistorySchema
from app.scraper.schemas.trip_schema import TripSchema
from app.scraper.logger import logger
from app.scraper.managers.http import send_request, get_response_size
from app.settings import settings


class BaseParser(ABC):
    def __init__(self, site: SiteModel):
        self.site = site
        self.date = datetime.today()
        self.currencies: dict[str, float] = {}

    @abstractmethod
    async def get_content(
        self,
        date: datetime,
        departure_city: CitySchema,
        arrival_city: CitySchema,
        **kwargs,
    ):
        """Fetches raw data from the website."""
        pass

    @abstractmethod
    def parse_data(
        self,
        content: TicketDataSchema,
        departure_city: CitySchema,
        arrival_city: CitySchema,
    ) -> List[TicketDataSchema]:
        """Parses the fetched data."""
        pass

    def convert_to_pydantic_models(self, trip: TicketDataSchema, route: dict) -> Dict:
        """Converts parsed data into Pydantic models."""
        try:
            route_data = RouteSchema(
                from_city_id=trip.from_city_id,
                to_city_id=trip.to_city_id,
                departure_date=trip.departure_datetime.date(),
                site_id=int(self.site.id),
                parsed_at=datetime.now(),
            )
            trip_data = TripSchema(
                from_station=trip.from_station_name,
                to_station=trip.to_station_name,
                departure_time=trip.departure_datetime.time(),
                arrival_time=(
                    trip.arrival_datetime.time() if trip.arrival_datetime else None
                ),
                arrival_date=(
                    trip.arrival_datetime.date() if trip.arrival_datetime else None
                ),
                carrier_name=trip.carrier_name,
                duration=trip.travel_time,
                is_transfer=bool(trip.is_transfer),
            )

            trip_history_data = TripHistorySchema(
                price=trip.price,
                currency=trip.currency,
                available_seats=trip.available_seats,
            )

            return {
                "route": route_data,
                "trip": trip_data,
                "trip_history": trip_history_data,
            }
        except ValidationError as e:
            logger.error(f"Data validation error: {e}")
            raise e


class RequestParser(BaseParser, ABC):
    def __init__(self, site: SiteModel):
        super().__init__(site)

    @classmethod
    @abstractmethod
    async def create(cls):
        """All subclasses must implement this method"""
        pass

    @classmethod
    async def load_site(cls, site_name: str) -> SiteModel:
        with settings.get_db() as session:
            site = session.query(SiteModel).filter(SiteModel.name == site_name).first()
            if not site or not site.is_active:
                raise ValueError(f"Site '{site_name}' not found or inactive.")
        return site

    async def init_async(self):
        pass

    @classmethod
    async def send_request(cls, *args, **kwargs):
        """Wrapper around the http_utils.send_request function."""
        response = await send_request(*args, **kwargs)

        return response

    async def get_content(
        self,
        date: datetime,
        departure_city: CitySchema,
        arrival_city: CitySchema,
        **kwargs,
    ):
        """
        Fetches raw data from the API or website.
        This method should be overridden in subclasses for specific logic.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def parse_data(
        self, response, departure_city: CitySchema, arrival_city: CitySchema
    ) -> List[TicketDataSchema]:
        """
        Parses the response data.
        This method should be overridden in subclasses for specific parsing logic.
        """
        raise NotImplementedError("Subclasses must implement this method.")
