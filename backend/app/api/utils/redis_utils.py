import json
from datetime import timedelta, datetime

from typing import Optional, Any

from backend.app.settings import settings


async def get_cache(key: str) -> Optional[Any]:
    async with settings.get_redis() as redis:
        cached_data = await redis.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None


def serialize_data(data: Any) -> Any:
    if isinstance(data, list):
        return [serialize_data(item) for item in data]
    elif hasattr(data, "__dict__"):
        item_dict = data.__dict__.copy()
        for key, value in item_dict.items():
            item_dict[key] = serialize_data(value)
        if "_sa_instance_state" in item_dict:
            item_dict.pop("_sa_instance_state")
        return item_dict
    elif isinstance(data, dict):
        return {k: serialize_data(v) for k, v in data.items()}
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data


async def set_cache(key: str, data: Any, expiration: timedelta):
    serialized_data = serialize_data(data)

    async with settings.get_redis() as redis:
        await redis.setex(
            key, int(expiration.total_seconds()), json.dumps(serialized_data)
        )


async def invalidate_cache(key: str):
    async with settings.get_redis() as redis:
        await redis.delete(key)
