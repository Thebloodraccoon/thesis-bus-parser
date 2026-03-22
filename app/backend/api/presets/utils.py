import json
from datetime import time
from typing import Any, List, Optional

import httpx  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.backend.api.cities.utils import CityCRUD
from app.backend.api.presets.schema import FilterPreset, FilterPresetCreate, FilterPresetUpdate
from app.backend.api.sites.utils import SiteCRUD
from app.backend.exceptions.filter_preset_exceptions import CitiesNotFoundException, SitesNotFoundException, \
    DuplicatePresetNameException, FiltersPresetNotFoundException
from app.backend.settings import settings, get_db


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, time):
            return obj.strftime("%H:%M")
        return super().default(obj)


def get_preset_key(user_id: int, preset_id: str) -> str:
    return f"user:{user_id}:filter_preset:{preset_id}"


def get_user_presets_key(user_id: int) -> str:
    return f"user:{user_id}:filter_presets"


class FilterPresetsCRUD:
    def __init__(self, db: Session):
        self.city_crud = CityCRUD(db)
        self.site_crud = SiteCRUD(db)

    def _validate_city(self, city_ids: Optional[List[int]]) -> None:
        if not city_ids:
            return
        existing_ids = set(self.city_crud.get_cities_ids_in_list(city_ids))
        missing_ids = set(city_ids) - existing_ids

        if missing_ids:
            raise CitiesNotFoundException(missing_ids)

    def _validate_sites(self, site_ids: Optional[List[int]]) -> None:
        if not site_ids:
            return

        existing_ids = set(self.site_crud.get_sites_ids_in_list(site_ids))
        missing_ids = set(site_ids) - existing_ids

        if missing_ids:
            raise SitesNotFoundException(missing_ids)

    async def _is_name_duplicate(
        self, user_id: int, name: str, exclude_preset_id: Optional[str] = None
    ) -> bool:
        presets = await self.get_presets(user_id)
        if not presets:
            return False

        for preset in presets:
            if preset.name == name and (
                exclude_preset_id is None or preset.id != exclude_preset_id
            ):
                return True

        return False

    async def create_preset(
        self, user_id: int, preset_data: FilterPresetCreate
    ) -> FilterPreset:
        if await self._is_name_duplicate(user_id, preset_data.name):
            raise DuplicatePresetNameException()

        self._validate_city(preset_data.from_cities)
        self._validate_city(preset_data.to_cities)
        self._validate_sites(preset_data.sites)

        new_preset = FilterPreset(
            name=preset_data.name,
            from_cities=preset_data.from_cities,
            to_cities=preset_data.to_cities,
            sites=preset_data.sites,
            is_transfer=preset_data.is_transfer,
            departure_from_time=preset_data.departure_from_time,
            departure_to_time=preset_data.departure_to_time,
            arrival_to_time=preset_data.arrival_to_time,
            arrival_from_time=preset_data.arrival_from_time,
        )

        async with settings.get_redis() as redis:
            preset_key = get_preset_key(user_id, new_preset.id)
            json_data = json.dumps(new_preset.model_dump(), cls=CustomJSONEncoder)

            await redis.set(preset_key, json_data)

            user_presets_key = get_user_presets_key(user_id)
            await redis.sadd(user_presets_key, new_preset.id)

        return new_preset

    @staticmethod
    async def get_presets(user_id: int) -> list[FilterPreset] | None:
        presets = []

        async with settings.get_redis() as redis:
            user_presets_key = get_user_presets_key(user_id)
            preset_ids = await redis.smembers(user_presets_key)

            for preset_id in preset_ids:
                preset_key = get_preset_key(user_id, preset_id)
                preset_data = await redis.get(preset_key)
                if preset_data:
                    presets.append(FilterPreset(**json.loads(preset_data)))

        return presets

    async def update_preset(
        self, user_id: int, preset_id: str, preset_update: FilterPresetUpdate
    ) -> FilterPreset:
        if preset_update.name is not None and await self._is_name_duplicate(
                user_id, preset_update.name, exclude_preset_id=preset_id
        ):
            raise DuplicatePresetNameException()

        async with settings.get_redis() as redis:
            preset_key = get_preset_key(user_id, preset_id)
            preset_data = await redis.get(preset_key)

            if not preset_data:
                raise FiltersPresetNotFoundException()

            current_preset = FilterPreset(**json.loads(preset_data))
            update_data = preset_update.model_dump(exclude_unset=True)

            if "from_cities" in update_data:
                self._validate_city(update_data["from_cities"])
            if "to_cities" in update_data:
                self._validate_city(update_data["to_cities"])
            if "sites" in update_data:
                self._validate_sites(update_data["sites"])

            for field, value in update_data.items():
                setattr(current_preset, field, value)

            await redis.set(
                preset_key,
                json.dumps(current_preset.model_dump(), cls=CustomJSONEncoder),
            )
            return current_preset

    @staticmethod
    async def delete_preset(user_id: int, preset_id: str) -> None:
        async with settings.get_redis() as redis:
            preset_key = get_preset_key(user_id, preset_id)
            preset_exists = await redis.exists(preset_key)

            if not preset_exists:
                raise FiltersPresetNotFoundException()

            user_presets_key = get_user_presets_key(user_id)
            await redis.srem(user_presets_key, preset_id)

            await redis.delete(preset_key)
