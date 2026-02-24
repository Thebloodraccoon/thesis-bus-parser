from typing import List, Optional, Union

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from parser.app.models import TripModel
from parser.app.schemas.trip_schema import TripSchema
from parser.app.settings.logger import get_logger

logger = get_logger(__name__)

class TripCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_trip_by_fields(
        self, first: bool = True, **filters
    ) -> Union[Optional[TripModel], List[TripModel]]:
        """
        Retrieves trips based on flexible fields. Can return either a single record or a list of records.
        """
        if not filters:
            raise ValueError("At least one field must be provided for filtering.")

        try:
            query = self.db.query(TripModel).filter(
                and_(
                    *[
                        getattr(TripModel, field) == value
                        for field, value in filters.items()
                    ]
                )
            )

            return query.first() if first else query.all()
        except Exception as e:
            logger.error(f"Error while querying trips with filters {filters}: {e}")
            return None if first else []

    def create_trip(self, trip_data: TripSchema, route_id: int) -> TripModel:
        """
        Creates a new trip record in the database.

        Args:
            trip_data (TripSchema): The data to create a trip.
            route_id (int): ID of the associated route.

        Returns:
            TripModel: The created trip model instance.
        """
        new_trip = TripModel(
            route_id=route_id,
            from_station=trip_data.from_station,
            to_station=trip_data.to_station,
            departure_time=trip_data.departure_time,
            arrival_time=(trip_data.arrival_time if trip_data.arrival_time else None),
            arrival_date=trip_data.arrival_date if trip_data.arrival_date else None,
            carrier_name=trip_data.carrier_name,
            duration=trip_data.duration,
            is_transfer=trip_data.is_transfer,
        )
        try:
            self.db.add(new_trip)
            self.db.commit()
            self.db.refresh(new_trip)
            return new_trip
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error while creating trip: {e}")
            raise Exception("Error occurred while saving the trip to the database.")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error while creating trip: {e}")
            raise

    def get_or_create_trip(self, trip_data: TripSchema, route_id: int) -> int:
        """
        Checks if a trip exists based on provided fields; if not, creates it.

        Args:
            trip_data (TripSchema): The data to check and create a trip if necessary.
            route_id (int): The ID of the associated route.

        Returns:
            int: The trip ID, either from an existing or newly created record.
        """
        try:
            existing_trip = self.get_trip_by_fields(
                first=True,
                route_id=route_id,
                departure_time=trip_data.departure_time,
                carrier_name=trip_data.carrier_name,
                from_station=trip_data.from_station,
                to_station=trip_data.to_station,
            )
            if isinstance(existing_trip, TripModel):
                return int(existing_trip.id)

            new_trip = self.create_trip(trip_data, route_id)
            return int(new_trip.id)
        except Exception as e:
            logger.error(f"Error in get_or_create_trip: {e}")
            raise
