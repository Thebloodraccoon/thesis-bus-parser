from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Any, Generator, Generic, List, Optional, Type, TypeVar

from sqlalchemy import and_, create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from thesis.core.models import (
    SiteModel,
    CityModel,
    CurrencyModel,
    RouteModel,
    TripModel,
    TripHistoryModel,
)
from thesis.parser.app.schemas import (
    CityCreate,
    CurrencySchema,
    RouteSchema,
    TripSchema,
    TripHistorySchema,
)
from thesis.parser.app.settings.config import settings
from thesis.parser.app.settings.logger import get_logger

logger = get_logger(__name__)

# Session factory
_engine = create_engine(settings.DATABASE_URL)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session: Session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()


# Generic repository base
M = TypeVar("M")


class BaseRepository(Generic[M]):
    """Generic CRUD repository.  Subclasses set ``model``."""

    model: Type[M]

    def __init__(self, session: Session) -> None:
        self._s = session

    def _get(self, **filters: Any) -> Optional[M]:
        return self._s.query(self.model).filter_by(**filters).first()

    def _all(self, **filters: Any) -> List[M]:
        return self._s.query(self.model).filter_by(**filters).all()

    def _add_and_flush(self, obj: M) -> M:
        try:
            self._s.add(obj)
            self._s.commit()
            self._s.refresh(obj)
            return obj
        except IntegrityError as exc:
            self._s.rollback()
            logger.error("IntegrityError: %s", exc)
            raise
        except Exception as exc:
            self._s.rollback()
            logger.error("Unexpected error: %s", exc)
            raise


# Domain repositories
class SiteRepository(BaseRepository[SiteModel]):
    model = SiteModel

    def get_by_name(self, name: str) -> Optional[SiteModel]:
        return self._get(name=name)

    def mark_parsed(self, name: str) -> None:
        site = self.get_by_name(name)
        if not site:
            raise ValueError(f"Site '{name}' not found.")

        site.last_parsed = datetime.now()  # type: ignore[assignment]
        self._s.commit()


class CityRepository(BaseRepository[CityModel]):
    model = CityModel

    def get_by_like_bus_id(self, like_bus_id: int) -> Optional[CityModel]:
        return self._get(like_bus_id=like_bus_id)

    def get_by_id(self, city_id: int) -> Optional[CityModel]:
        return self._get(id=city_id)

    def create(self, data: CityCreate) -> CityModel:
        return self._add_and_flush(CityModel(**data.model_dump()))

    def update_or_create(self, data: CityCreate) -> CityModel:
        existing = self.get_by_like_bus_id(data.like_bus_id)

        if existing:
            for key, value in data.model_dump().items():
                if value is not None:
                    setattr(existing, key, value)

            self._s.commit()
            return existing

        return self.create(data)

    def set_site_city_id(self, city_id: int, field_name: str, value: Any) -> bool:
        """Update a site-specific city-ID field (e.g. ``inbus_id``)."""
        city = self.get_by_id(city_id)
        if city is None:
            return False

        setattr(city, field_name, value)
        self._s.commit()
        return True

    def all_active(self) -> List[CityModel]:
        """Return all cities that are not test entries."""
        cities = self._all()
        return [
            c
            for c in cities
            if "тест" not in (c.name_ua or "").lower()
            and "test" not in (c.name_ua or "").lower()
        ]

    def fix_sequence(self) -> None:
        self._s.execute(
            text("SELECT setval('cities_id_seq', (SELECT MAX(id) FROM cities))")
        )
        self._s.commit()


class CurrencyRepository(BaseRepository[CurrencyModel]):
    model = CurrencyModel

    def get_by_code(self, code: str) -> Optional[CurrencyModel]:
        return self._get(code=code.upper())

    def update_or_create(self, data: CurrencySchema) -> CurrencyModel:
        existing = self.get_by_code(data.code)
        if existing:
            existing.rate = data.rate  # type: ignore
            existing.exchange_date = data.exchange_date  # type: ignore
            self._s.commit()
            self._s.refresh(existing)
            return existing

        return self._add_and_flush(
            CurrencyModel(
                code=data.code.upper(),
                rate=data.rate,
                exchange_date=data.exchange_date,
            )
        )


class RouteRepository(BaseRepository[RouteModel]):
    model = RouteModel

    def get_or_create(self, data: RouteSchema) -> int:
        existing = (
            self._s.query(RouteModel)
            .filter(
                and_(
                    RouteModel.from_city_id == data.from_city_id,
                    RouteModel.to_city_id == data.to_city_id,
                    RouteModel.departure_date == data.departure_date,
                    RouteModel.site_id == data.site_id,
                )
            )
            .first()
        )

        if existing:
            return int(existing.id)

        return int(
            self._add_and_flush(
                RouteModel(
                    from_city_id=data.from_city_id,
                    to_city_id=data.to_city_id,
                    departure_date=data.departure_date,
                    site_id=data.site_id,
                    parsed_at=data.parsed_at or datetime.now(),
                )
            ).id
        )


class TripRepository(BaseRepository[TripModel]):
    model = TripModel

    def get_or_create(self, data: TripSchema, route_id: int) -> int:
        existing = (
            self._s.query(TripModel)
            .filter(
                and_(
                    TripModel.route_id == route_id,
                    TripModel.departure_time == data.departure_time,
                    TripModel.carrier_name == data.carrier_name,
                    TripModel.from_station == data.from_station,
                    TripModel.to_station == data.to_station,
                )
            )
            .first()
        )

        if existing:
            return int(existing.id)

        return int(
            self._add_and_flush(
                TripModel(
                    route_id=route_id,
                    from_station=data.from_station,
                    to_station=data.to_station,
                    departure_time=data.departure_time,
                    arrival_time=data.arrival_time,
                    arrival_date=data.arrival_date,
                    carrier_name=data.carrier_name,
                    duration=data.duration,
                    is_transfer=data.is_transfer,
                )
            ).id
        )


class TripHistoryRepository(BaseRepository[TripHistoryModel]):
    model = TripHistoryModel

    def create_if_changed(
        self, data: TripHistorySchema, trip_id: int
    ) -> type[TripHistoryModel] | TripHistoryModel:
        """Skip duplicate price snapshots."""
        existing = (
            self._s.query(TripHistoryModel)
            .filter(
                and_(
                    TripHistoryModel.trip_id == trip_id,
                    TripHistoryModel.price == data.price,
                    TripHistoryModel.currency == data.currency,
                    TripHistoryModel.available_seats == data.available_seats,
                )
            )
            .first()
        )

        if existing:
            return existing

        return self._add_and_flush(
            TripHistoryModel(
                trip_id=trip_id,
                price=data.price,
                currency=data.currency,
                available_seats=data.available_seats,
            )
        )
