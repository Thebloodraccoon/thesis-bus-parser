from sqlalchemy import Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from thesis.core.base import Base, TimestampMixin  # noqa


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
