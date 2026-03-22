from typing import Any, Optional

from pydantic import ValidationError  # type: ignore
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.models import CityModel
from app.parser.db.db_helper import update_if_changed
from app.parser.managers.http.likebus_api import get_cities
from app.parser.schemas.city_schema import CityCreate, CitySchema
from app.parser.settings.logger import get_logger

logger = get_logger(__name__)   

class CityCRUD:
    @staticmethod
    def prepare_city_info(city_data: dict) -> CityCreate:
        """Prepares and validates city information from API data."""
        try:
            # Ensure data is properly cast before creating schema
            like_bus_id = int(city_data["id"])
            name_ua = city_data["loc"]["ua"].get("name", "")
            name_en = city_data["loc"]["en"].get("name", "")

            # Validate that at least one name is non-empty
            if not any([name_ua.strip(), name_en.strip()]):
                raise ValueError("All city names are missing or empty.")

            return CityCreate(  # type: ignore
                like_bus_id=like_bus_id,
                name_ua=name_ua,
                name_en=name_en,
            )
        except (ValueError, KeyError) as e:
            logger.error(f"Invalid city data: {city_data}. Error: {e}")
            raise ValueError(f"City data validation failed: {e}")

    @staticmethod
    def get_city_by_field(db: Session, field: str, value: Any) -> Optional[CityModel]:
        """Fetches a city by a given field."""
        return db.query(CityModel).filter(getattr(CityModel, field) == value).first()

    @staticmethod
    def update_existing_city(
        existing_city: CityModel, validated_city: CityCreate
    ) -> bool:
        """Updates an existing city by modifying only specific fields."""
        fields_to_update = ["name_ua", "name_en", "like_bus_id"]

        updated = update_if_changed(
            existing_city,
            validated_city.model_dump(),
            fields_to_update=fields_to_update,
        )

        if updated:
            logger.info(
                f"Updated city {validated_city.name_ua} with LikeBus ID {validated_city.like_bus_id}."
            )
        return updated

    @classmethod
    def fix_sequence(cls, db: Session) -> None:
        """Fix the sequence for the cities table."""
        try:
            db.execute(
                text("SELECT setval('cities_id_seq', (SELECT MAX(id) FROM cities))")
            )
            db.commit()
            logger.info("Cities sequence has been synchronized.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error fixing sequence: {e}")

    @staticmethod
    def add_new_city(db: Session, validated_city: CityCreate) -> CityModel:
        """Adds a new city to the database."""
        db_city = CityModel(**validated_city.model_dump())
        db.add(db_city)
        db.commit()
        logger.info(
            f"Added new city {validated_city.name_ua} with LikeBus ID {validated_city.like_bus_id}."
        )
        return db_city

    @classmethod
    def save_city(cls, db: Session, city_data: dict):
        """Validates, checks existence, and adds/updates a city."""
        validated_city = cls.prepare_city_info(city_data)

        existing_city = cls.get_city_by_field(
            db, "like_bus_id", validated_city.like_bus_id
        )
        if existing_city:
            cls.update_existing_city(existing_city, validated_city)
        else:
            cls.add_new_city(db, validated_city)

    @classmethod
    def save_cities(cls, db: Session) -> None:
        """Fetches cities from API and saves them to the database."""

        # Synchronize the sequence before starting work
        cls.fix_sequence(db)

        cities_data = get_cities()
        if not cities_data:
            logger.error("No cities data received from API.")
            return
        try:
            for city_data in cities_data:
                try:
                    cls.save_city(db, city_data)
                except ValidationError:
                    continue
            db.commit()
            logger.info("All cities have been processed and saved to the database.")
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error: {e}")

    @classmethod
    def get_city(cls, db: Session, field: str, value: Any) -> Optional[CitySchema]:
        """Fetches a city by a given field and returns it as a Pydantic schema."""
        city = cls.get_city_by_field(db, field, value)
        return CitySchema.model_validate(city) if city else None

    @classmethod
    def get_city_by_like_bus_id(cls, db, like_bus_id: int) -> Optional[CitySchema]:
        """Fetches a city by its LikeBus ID."""
        return cls.get_city(db, "like_bus_id", like_bus_id)


city_crud = CityCRUD()
