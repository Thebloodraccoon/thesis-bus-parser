from typing import List, Optional, Union

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.models import  TripHistoryModel
from app.parser.schemas.trip_history_schema import TripHistorySchema
from app.parser.settings.logger import get_logger

logger = get_logger(__name__)


class TripHistoryCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_trip_history_by_fields(
        self, first: bool = True, **filters
    ) -> Union[Optional[TripHistoryModel], List[TripHistoryModel]]:
        """
        Retrieves trip histories based on flexible fields. Can return either a single record or a list of records.

        Args:
            first (bool): If True, returns only the first matching record; otherwise, returns all matching records.
            **filters: Arbitrary keyword arguments representing the fields to filter by.

        Returns:
            TripHistoryModel or List[TripHistoryModel] or None: The existing trip history record(s) if found, otherwise None.
        """
        if not filters:
            raise ValueError("At least one field must be provided for filtering.")

        try:
            query = self.db.query(TripHistoryModel).filter(
                and_(
                    *[
                        getattr(TripHistoryModel, field) == value
                        for field, value in filters.items()
                    ]
                )
            )
            return query.first() if first else query.all()
        except Exception as e:
            logger.error(f"❌ Error querying trip history with filters {filters}: {e}")
            return None if first else []

    def create_trip_history(
        self, trip_history_data: TripHistorySchema, trip_id: int
    ) -> TripHistoryModel:
        """
        Creates a new trip history record in the database.

        Args:
            trip_history_data (TripHistorySchema): The data to create a trip history.
            trip_id (int): ID of the associated trip.

        Returns:
            TripHistoryModel: The created trip history model instance.
        """

        existing_record = self.get_trip_history_by_fields(
            first=True,
            trip_id=trip_id,
            price=trip_history_data.price,
            currency=trip_history_data.currency,
            available_seats=trip_history_data.available_seats,
        )

        if existing_record:
            logger.info(
                f"Trip history record already exists for trip_id {trip_id}. Skipping creation."
            )
            return existing_record

        new_trip_history = TripHistoryModel(
            trip_id=trip_id,
            price=trip_history_data.price,
            currency=trip_history_data.currency,
            available_seats=trip_history_data.available_seats,
        )

        try:
            self.db.add(new_trip_history)
            self.db.commit()
            self.db.refresh(new_trip_history)
            return new_trip_history
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error while creating trip history: {e}")
            raise Exception("Database integrity error occurred.")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error while creating trip history: {e}")
            raise
