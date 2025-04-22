from sqlalchemy import Column, Integer, String

from .meta import Base


class City(Base):
    __tablename__ = "cities"

    city_id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
