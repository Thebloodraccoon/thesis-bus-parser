from sqlalchemy import Column, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.models.base import TimestampMixin
from app.settings import settings


class TripHistoryModel(settings.Base, TimestampMixin):
    __tablename__ = "trip_history"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(
        Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    price = Column(Numeric, nullable=False, index=True)
    currency = Column(String(5), nullable=False, index=True)
    available_seats = Column(Integer, nullable=True)

    trip = relationship("TripModel", back_populates="trip_history")

    __table_args__ = (Index("idx_trip_history_trip_created", "trip_id", "created_at"),)
