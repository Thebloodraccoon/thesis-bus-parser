from sqlalchemy import BigInteger, Column, Integer, String

from app.core.base import Base


class CityModel(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    like_bus_id = Column(Integer, nullable=False)
    name_ua = Column(String)
    name_en = Column(String)
    ukrpas_id = Column(Integer)
    inbus_id = Column(BigInteger)
    rubikon_id = Column(Integer)
    voyager_id = Column(Integer)
