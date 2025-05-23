from sqlalchemy import Column, Integer, String

from .meta import Base


class Interest(Base):
    __tablename__ = "interests"

    interest_id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
