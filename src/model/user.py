from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, Integer, String
from sqlalchemy.sql import func

from .meta import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(64), unique=True)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64))
    age = Column(Integer)
    gender = Column(String(10))
    city_id = Column(Integer, ForeignKey("cities.city_id"))
    created_at = Column(TIMESTAMP, server_default=func.now())
