from datetime import timedelta
from typing import List

from sqlalchemy import select  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from backend.app.api.cities.schema import CitySchema
from backend.app.api.models import CityModel
from backend.app.api.utils.redis_utils import get_cache, set_cache, invalidate_cache

ALL_CITIES_CACHE_KEY = "cities:"
CITIES_CACHE_EXPIRATION = timedelta(days=1)


async def get_all_cached_cities(db: Session) -> List[CitySchema]:
    cached_data = await get_cache(ALL_CITIES_CACHE_KEY)
    if cached_data:
        return cached_data

    cities = CityCRUD(db).get_all_cities()
    sorted_cities = sorted(cities, key=lambda city: city.id)

    await set_cache(ALL_CITIES_CACHE_KEY, sorted_cities, CITIES_CACHE_EXPIRATION)

    return sorted_cities


async def update_city_cache(db: Session) -> None:
    await invalidate_cache(ALL_CITIES_CACHE_KEY)
    await get_all_cached_cities(db)


class CityCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_all_cities(self) -> List[CitySchema]:
        stmt = select(CityModel)
        cities = self.db.execute(stmt).scalars().all()

        result = []
        for city in cities:
            result.append(
                CitySchema(
                    id=city.id,
                    name_en=city.name_en,
                    name_ua=city.name_ua,
                    like_bus_id=city.like_bus_id
                )
            )
        return result

    def get_cities_ids_in_list(self, ids: List[int]) -> List[int]:
        if not ids:
            return []

        stmt = select(CityModel.id).where(CityModel.id.in_(ids))
        return list(self.db.execute(stmt).scalars().all())
