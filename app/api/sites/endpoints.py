from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.auth.utils import get_current_user, admin_only
from app.models import User
from app.scraper.sites.cache import get_cached_sites, invalidate_site_caches
from app.scraper.sites.schema import SiteResponse, SiteCreate, SiteUpdate
from app.scraper.sites.utils import SiteCRUD
from app.settings import settings

router = APIRouter(prefix="/sites", tags=["Sites"])


@router.get("/", response_model=List[SiteResponse])
async def get_all_sites(
    is_site_active: Optional[bool] = Query(
        None,
        description="Фильтр по активности сайтов. "
        "True - только активные сайты, "
        "False - только неактивные сайты",
    ),
    db: Session = Depends(settings.get_scraper_db),
    _: User = Depends(get_current_user),
):
    sites = await get_cached_sites(db, is_site_active=is_site_active)
    return sites


@router.get("/{site_id}", response_model=SiteResponse)
def get_site_by_id(
    site_id: int,
    db: Session = Depends(settings.get_scraper_db),
    _: User = Depends(get_current_user),
):
    site = SiteCRUD(db).get_site_by_id(site_id=site_id)
    return site


@router.post("/", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
async def create_site(
    site_data: SiteCreate,
    db: Session = Depends(settings.get_scraper_db),
    _: User = Depends(admin_only),
):
    new_site = SiteCRUD(db).create_site(site_data=site_data)
    await invalidate_site_caches()
    return new_site


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(
    site_id: int,
    db: Session = Depends(settings.get_scraper_db),
    _: User = Depends(admin_only),
):
    SiteCRUD(db).delete_site(site_id=site_id)
    await invalidate_site_caches()


@router.put("/{site_id}", response_model=SiteResponse, status_code=status.HTTP_200_OK)
async def update_site(
    site_id: int,
    site_data: SiteUpdate,
    db: Session = Depends(settings.get_scraper_db),
    _: User = Depends(admin_only),
):
    updated_site = SiteCRUD(db).update_site(site_id=site_id, site_data=site_data)
    await invalidate_site_caches()
    return updated_site
