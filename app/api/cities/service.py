from datetime import timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.utils.redis_cache import get_cache, set_cache, invalidate_cache
from app.models import CityModel
from app.schemas.city_schema import CitySchema

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
        result = self.db.execute(select(CityModel)).all()

        cities_dict = {}
        for city, station in result:
            if city.id not in cities_dict:
                city.stations = []
                cities_dict[city.id] = city
            if station:
                cities_dict[city.id].stations.append(station)

        return list(cities_dict.values())

    def get_cities_ids_in_list(self, ids: List[int]) -> List[int]:
        if not ids:
            return []

        stmt = select(CityModel.id).where(CityModel.id.in_(ids))
        return list(self.db.execute(stmt).scalars().all())
