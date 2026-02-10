from typing import List, Optional  # type: ignore

from fastapi import HTTPException, status  # type: ignore

from app.exceptions.scraper_exceptions import SiteNotFound
from app.scraper.models import SiteModel

from sqlalchemy.orm import Session  # type: ignore
from sqlalchemy import select  # type: ignore

from app.scraper.sites.schema import SiteCreate, SiteUpdate


class SiteCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_all_sites(self, is_site_active: Optional[bool] = None) -> List[SiteModel]:
        query = self.db.query(SiteModel)

        if is_site_active is not None:
            query = query.filter(SiteModel.is_active == is_site_active)

        return query.all()

    def get_site_by_id(self, site_id: int) -> Optional[SiteModel]:
        site = self.db.query(SiteModel).filter(SiteModel.id == site_id).first()
        if not site:
            raise SiteNotFound(site_id)
        return site

    def get_site_by_name(self, name: str) -> Optional[SiteModel]:
        site = self.db.query(SiteModel).filter(SiteModel.name == name).first()
        if not site:
            raise SiteNotFound(name=name)
        return site

    def create_site(self, site_data: SiteCreate) -> SiteModel:
        new_site = SiteModel(
            name=site_data.name,
            url=site_data.url,
            is_active=site_data.is_active,
            api_key=site_data.api_key,
            is_aggregator=site_data.is_aggregator,
            depth=site_data.depth,
            threads=site_data.threads,
        )
        self.db.add(new_site)
        self.db.commit()
        self.db.refresh(new_site)
        return new_site

    def delete_site(self, site_id: int) -> None:
        site_to_delete = (
            self.db.query(SiteModel).filter(SiteModel.id == site_id).first()
        )

        if not site_to_delete:
            raise SiteNotFound(site_id)

        self.db.delete(site_to_delete)
        self.db.commit()

    def update_site(self, site_id: int, site_data: SiteUpdate) -> SiteModel:
        site_to_update = (
            self.db.query(SiteModel).filter(SiteModel.id == site_id).first()
        )

        if not site_to_update:
            raise SiteNotFound(site_id)

        update_data = site_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(site_to_update, key, value)

        self.db.commit()
        self.db.refresh(site_to_update)
        return site_to_update

    def get_sites_ids_in_list(self, ids: List[int]) -> List[int]:
        if not ids:
            return []

        stmt = select(SiteModel.id).where(SiteModel.id.in_(ids))
        return list(self.db.execute(stmt).scalars().all())
