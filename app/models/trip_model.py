from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Interval,
    String,
    Time,
)
from sqlalchemy.orm import relationship

from app.models.base import TimestampMixin
from app.settings import settings


class TripModel(settings.Base, TimestampMixin):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(
        Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_station = Column(String, nullable=True, index=True)
    to_station = Column(String, nullable=True, index=True)
    departure_time = Column(Time, nullable=False, index=True)
    arrival_time = Column(Time, nullable=True)
    arrival_date = Column(Date, nullable=True, index=True)
    carrier_name = Column(String, nullable=False, index=True)
    duration = Column(Interval, nullable=True)
    is_transfer = Column(Boolean, default=False, index=True)

    trip_history = relationship(
        "TripHistoryModel",
        back_populates="trip",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    route = relationship("RouteModel", back_populates="trips")

    __table_args__ = (Index("idx_trips_route_departure", "route_id", "departure_time"),)
