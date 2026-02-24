from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from parser.app.models.base import TimestampMixin
from parser.app.settings.conf import Base


class TripHistoryModel(Base, TimestampMixin):
    __tablename__ = "trip_history"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(
        Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    price = Column(Numeric, nullable=False)
    currency = Column(String(5), nullable=False)
    available_seats = Column(Integer, nullable=True)

    trip = relationship("TripModel", back_populates="trip_history")
