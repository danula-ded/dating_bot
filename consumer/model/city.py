from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from consumer.model.meta import Base


class City(Base):
    """Model for storing cities."""

    __tablename__ = 'cities'

    city_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    users = relationship('User', back_populates='city')

    def __repr__(self):
        return f"<City(city_id={self.city_id}, name='{self.name}')>"
