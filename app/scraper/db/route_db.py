import json
from datetime import datetime, timedelta
from typing import List, Optional, Type, Union

from sqlalchemy import String, and_, cast, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import RouteModel
from app.schemas.route_schema import RouteSchema
from app.scraper.db.db_helper import optimize_postgres
from app.scraper.logger import logger


class RouteCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_route_by_fields(  # noqa: C901
        self, first: bool = True, **filters
    ) -> Union[Optional[RouteModel], List[RouteModel]]:
        """
        Retrieves routes based on flexible fields. Can return a single record or a list of records.

        Args:
            first (bool): If True, returns only the first matching record; otherwise, returns all matching records.
            **filters: Arbitrary keyword arguments representing the fields to filter by.

        Returns:
            RouteModel or List[RouteModel] or None: The existing route(s) if found, otherwise None.
        """
        if not filters:
            raise ValueError("At least one field must be provided for filtering.")

        filter_conditions = []
        if "likebus_trip_ids" in filters and filters["likebus_trip_ids"] is not None:
            if isinstance(filters["likebus_trip_ids"], list):
                filters["likebus_trip_ids"] = json.dumps(filters["likebus_trip_ids"])

            likebus_trip_ids_value = filters.pop("likebus_trip_ids")
            filter_conditions.append(
                cast(RouteModel.likebus_trip_ids, String) == likebus_trip_ids_value
            )

        for field, value in filters.items():
            if "__" in field:
                field_name, operator = field.split("__", 1)
                column = getattr(RouteModel, field_name, None)

                if column is None:
                    raise AttributeError(
                        f"Model 'RouteModel' has no attribute '{field_name}'"
                    )

                if operator == "lt":
                    filter_conditions.append(column < value)
                elif operator == "lte":
                    filter_conditions.append(column <= value)
                elif operator == "gt":
                    filter_conditions.append(column > value)
                elif operator == "gte":
                    filter_conditions.append(column >= value)
                elif operator == "neq":
                    filter_conditions.append(column != value)
                else:
                    raise ValueError(f"Unsupported filter operator: {operator}")
            else:
                filter_conditions.append(getattr(RouteModel, field) == value)

        query = self.db.query(RouteModel).filter(and_(*filter_conditions))

        return query.first() if first else query.all()

    def create_route(self, route_data: RouteSchema) -> RouteModel:
        """
        Creates a new route record in the database.

        Args:
            route_data (RouteSchema): The data to create a route.

        Returns:
            RouteModel: The created route model instance.
        """
        new_route = RouteModel(
            from_city_id=route_data.from_city_id,
            to_city_id=route_data.to_city_id,
            departure_date=route_data.departure_date,
            site_id=route_data.site_id,
            parsed_at=route_data.parsed_at or datetime.now(),
        )
        try:
            self.db.add(new_route)
            self.db.commit()
            self.db.refresh(new_route)
            return new_route
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error while creating route: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error while creating route: {e}")
            raise

    def get_or_create_route(self, route_data: RouteSchema) -> int:
        """
        Checks if a route exists based on provided fields; if not, creates it.

        Args:
            route_data (RouteSchema): The data to check and create a route if necessary.

        Returns:
            int: The route ID, either from an existing or newly created record.
        """
        try:
            existing_route = self.get_route_by_fields(
                from_city_id=route_data.from_city_id,
                to_city_id=route_data.to_city_id,
                departure_date=route_data.departure_date,
                site_id=route_data.site_id,
                likebus_route_id=route_data.likebus_route_id,
                likebus_trip_ids=route_data.likebus_trip_ids,
            )
            if isinstance(existing_route, RouteModel):
                return int(existing_route.id)

            return int(self.create_route(route_data).id)
        except Exception as e:
            logger.error(f"Error in get_or_create_route: {e}")
            raise

    def fetch_old_routes(
        self, batch_size: int = 100, last_id: int = 0
    ) -> list[Type[RouteModel]]:
        """
        Получает маршруты, созданные более 30 дней назад, без OFFSET.
        """
        thirty_days_ago = datetime.now() - timedelta(days=30)
        return (
            self.db.query(RouteModel)  # type: ignore
            .filter(RouteModel.parsed_at < thirty_days_ago)
            .filter(RouteModel.id > last_id)
            .order_by(RouteModel.id)
            .limit(batch_size)
            .all()
        )

    def get_all_routes(self) -> List[RouteModel]:
        """
        Получает все маршруты из базы данных.

        Returns:
            List[RouteModel]: Список всех маршрутов.
        """
        return self.db.query(RouteModel).all()

    def delete_routes_by_ids(self, route_ids: List[int], batch_size: int = 1000):
        """
        Deletes routes in batches (trips and trip_history are automatically removed via ON DELETE CASCADE).
        """
        if not route_ids:
            logger.info("✅ No routes to delete.")
            return

        try:
            for i in range(0, len(route_ids), batch_size):
                batch = route_ids[i : i + batch_size]
                self.db.execute(
                    text(
                        """
                        DELETE FROM routes
                        USING unnest(:route_ids) AS r(id)
                        WHERE routes.id = r.id;
                    """
                    ),
                    {"route_ids": batch},
                )
                self.db.commit()
                logger.info(f"🔥 Deleted routes: {len(batch)}")
                optimize_postgres()
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error deleting routes: {e}")
            raise
