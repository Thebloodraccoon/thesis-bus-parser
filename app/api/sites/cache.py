from datetime import timedelta
from typing import Optional, List

from sqlalchemy.orm import Session  # type: ignore

from app.scraper.sites.utils import SiteCRUD
from app.scraper.utils.utils import (
    get_cache,
    set_cache,
    serialize_data,
    invalidate_cache,
)

CACHE_EXPIRATION = timedelta(hours=1)


def get_site_cache_key(is_site_active: Optional[bool]) -> str:
    return f"sites:all:{is_site_active}"


async def get_cached_sites(
    db: Session, is_site_active: Optional[bool] = None
) -> List[dict]:
    cache_key = get_site_cache_key(is_site_active)
    cached = await get_cache(cache_key)
    if cached is not None:
        return cached

    site_crud = SiteCRUD(db)
    sites = site_crud.get_all_sites(is_site_active)
    serialized = serialize_data(sites)
    await set_cache(cache_key, serialized, CACHE_EXPIRATION)
    return serialized


async def invalidate_site_caches():
    for state in ("None", "True", "False"):
        await invalidate_cache(f"sites:all:{state}")
