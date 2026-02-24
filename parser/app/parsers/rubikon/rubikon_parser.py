from datetime import datetime
from typing import List, Dict, Any, Tuple

from parser.app.models import SiteModel
from parser.app.parsers.base_parser import RequestParser
from parser.app.parsers.rubikon.rubikon_helper import parse_trip_data
from parser.app.parsers.utils import convert_ticket_to_uah
from parser.app.schemas.city_schema import CitySchema
from parser.app.schemas.ticket_schema import TicketDataSchema
from parser.app.settings.logger import get_logger

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

    async def _fetch_page(
        self, url: str, params: dict, headers: dict, page: int
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        A helper method for retrieving single-page data.
        Returns the tuple: (list of tickets, total number of tickets).
        """

        current_params = params.copy()
        current_params["page"] = page

        response = await self.send_request(
            url=url,
            method="GET",
            params=current_params,
            headers=headers,
            timeout=120,
            follow_redirects=True,
        )

        if not response or response.status_code != 200:
            logger.warning(
                f"Failed to fetch page {page}: status {response.status_code if response else 'None'}"
            )
            return [], 0

        data = response.json()
        if not data.get("status", "").endswith("success"):
            logger.warning(
                f"API returned non-success status on page {page}: {data.get('status')}"
            )
            return [], 0

        departures_data = data.get("data", {})
        tickets = departures_data.get("departures", {}).get("data", [])
        total_count = departures_data.get("departuresCount", 0)

        return tickets, total_count

    async def get_content(
        self,
        date: datetime,
        departure_city: CitySchema,
        arrival_city: CitySchema,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        url = f"{self.site.url}/departures"
        all_tickets = []

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

            first_page_tickets, total_departures = await self._fetch_page(
                url, params, headers, page=1
            )

            if not first_page_tickets:
                return all_tickets

            all_tickets.extend(first_page_tickets)
            per_page = len(first_page_tickets)
            if total_departures <= per_page:
                return all_tickets

            total_pages = (total_departures + per_page - 1) // per_page
            logger.info(
                f"Found {total_departures} tickets, parsing {total_pages} pages."
            )

            for page in range(2, total_pages + 1):
                tickets, _ = await self._fetch_page(url, params, headers, page)
                if tickets:
                    all_tickets.extend(tickets)
                else:
                    logger.warning(f"No tickets found on page {page} (unexpected)")

            return all_tickets

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
