import asyncio
from datetime import datetime
from typing import Dict

from app.scraper.db.route_db import RouteCRUD
from app.scraper.db.trip_db import TripCRUD
from app.scraper.db.trip_history_db import TripHistoryCRUD
from app.scraper.schemas.route_schema import RouteSchema
from app.scraper.schemas.trip_history_schema import TripHistorySchema
from app.scraper.schemas.trip_schema import TripSchema
from app.scraper.schemas.types import RouteData, ParsingResult
from app.settings.conf import get_db
from app.settings.logger import get_logger, handle_processing_error

logger = get_logger(__name__)


class RouteProcessingManager:
    def __init__(self, parser_class):
        self.parser_class = parser_class

    async def process_single_route(
        self,
        route: RouteData,
        selected_date,
        max_duration_seconds: int = None,
        start_time: datetime = None,
    ) -> Dict:
        """Processes one route and returns statistics delta."""

        stats = {"success": 0, "error": 0}

        try:
            if max_duration_seconds and start_time:
                if (
                    datetime.now() - start_time
                ).total_seconds() >= max_duration_seconds:
                    return {
                        "result": ParsingResult(success=False),
                        "stats": stats,
                        "date": selected_date,
                    }

            content = await self.parser_class.get_content(
                selected_date, route.departure_city, route.arrival_city
            )

            parsed_data = self.parser_class.parse_data(
                content, route.departure_city, route.arrival_city
            )

            if parsed_data:
                await asyncio.to_thread(
                    self._save_tickets_to_db, parsed_data, route
                )

            stats["success"] = 1
            return {
                "result": ParsingResult(success=True),
                "stats": stats,
                "date": selected_date,
            }

        except Exception as e:
            handle_processing_error(
                e, route.departure_city, route.arrival_city, self.parser_class.site.name
            )
            stats["error"] = 1
            return {
                "result": ParsingResult(success=False, error=str(e)),
                "stats": stats,
                "date": selected_date,
            }

    def _save_tickets_to_db(self, parsed_data, route):
        try:
            if hasattr(route, "dict"):
                route_dict = route.dict()

            elif hasattr(route, "model_dump"):
                route_dict = route.model_dump()

            elif hasattr(route, "__dict__"):
                route_dict = route.__dict__
            else:
                route_dict = route

            for ticket in parsed_data:
                data = self.parser_class.convert_to_pydantic_models(ticket, route_dict)
                self.save_data(data)

            logger.info(f"Successfully saved {len(parsed_data)} tickets")
        except Exception as e:
            logger.error(f"Error saving tickets: {e}")

    @classmethod
    def save_data(
        cls, parsed_data: Dict[str, RouteSchema | TripSchema | TripHistorySchema]
    ):
        """Saves parsed data to the database."""

        with get_db() as session:
            route_crud = RouteCRUD(db=session)
            trip_crud = TripCRUD(db=session)
            trip_history_crud = TripHistoryCRUD(db=session)

            route_data = parsed_data["route"]
            if isinstance(route_data, RouteSchema):
                route_id = route_crud.get_or_create_route(route_data)

            trip_data = parsed_data["trip"]
            if isinstance(trip_data, TripSchema):
                trip_id = trip_crud.get_or_create_trip(trip_data, route_id)

            trip_history_data = parsed_data["trip_history"]
            if isinstance(trip_history_data, TripHistorySchema):
                trip_history_id = trip_history_crud.create_trip_history(
                    trip_history_data, trip_id
                )

        return {
            "route_id": route_id,
            "trip_id": trip_id,
            "trip_history_id": trip_history_id,
        }
