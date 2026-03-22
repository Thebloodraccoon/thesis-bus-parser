from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.core.base import Base # noqa

class SiteModel(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    last_parsed = Column(DateTime)
    is_active = Column(Boolean, nullable=False, default=True)