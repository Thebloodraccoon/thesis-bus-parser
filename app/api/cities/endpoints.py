from fastapi import APIRouter, Depends  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.api.auth.utils import get_current_user, admin_only
from app.api.cities.service import get_all_cached_cities, update_city_cache
from app.models import User
from app.settings import settings

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
