from fastapi import APIRouter, Depends  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from backend.app.api.auth.utils import get_current_user, admin_only
from backend.app.api.cities.utils import get_all_cached_cities, update_city_cache
from backend.app.models.users import User
from backend.app.settings import settings

router = APIRouter(prefix="/cities", tags=["Cities"])


@router.get("/")
async def get_all_cities(
    db: Session = Depends(settings.get_scraper_db),
    _: User = Depends(get_current_user),
):
    return await get_all_cached_cities(db)


@router.post("/refresh-cache")
async def refresh_cities_cache(
    db: Session = Depends(settings.get_scraper_db),
    _: User = Depends(admin_only),
):
    await update_city_cache(db)

    return {"message": "Кеш городов успешно обновлен"}
