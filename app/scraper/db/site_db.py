from datetime import datetime
from typing import Optional

from app.settings.conf import get_db
from app.models import SiteModel


def get_site_by_name(name: str) -> Optional[SiteModel]:
    """Fetches a site by its name from the database and returns it as a Pydantic schema."""
    with get_db() as db:
        site = db.query(SiteModel).filter(SiteModel.name == name).first()

        if site:
            return site
        return None


def write_last_parsed(site_name: str) -> None:
    """Updates the last_parsed field for a site."""
    with get_db() as db:
        site = db.query(SiteModel).filter(SiteModel.name == site_name).first()
        if site:
            site.last_parsed = datetime.now()  # type: ignore
            db.commit()
        else:
            raise Exception(f"Site {site_name} not found in database.")
