from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer
from sqlalchemy.orm import relationship

from parser.app.models.base import TimestampMixin
from parser.app.settings.conf import Base


class RouteModel(Base, TimestampMixin):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    from_city_id = Column(
        Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    to_city_id = Column(
        Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    departure_date = Column(Date, nullable=False, index=True)
    site_id = Column(
        Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parsed_at = Column(DateTime, index=True)

    trips = relationship(
        "TripModel",
        back_populates="route",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index(
            "idx_routes_from_to_date", "from_city_id", "to_city_id", "departure_date"
        ),
    )
