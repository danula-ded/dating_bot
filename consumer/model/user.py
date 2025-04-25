from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, func, BigInteger, ForeignKey
from sqlalchemy.orm import relationship

from consumer.model.meta import Base


class User(Base):
    """Модель пользователя."""
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(64), unique=True)
    first_name = Column(String(64), nullable=False)
    age = Column(Integer)
    gender = Column(String(10))
    city_id = Column(Integer, ForeignKey('cities.city_id'))
    created_at = Column(DateTime, server_default=func.now())

    # Отношения для лайков и дизлайков
    likes_given = relationship(
        'Like',
        foreign_keys='Like.user_id',
        back_populates='user'
    )
    likes_received = relationship(
        'Like',
        foreign_keys='Like.target_user_id',
        back_populates='target_user'
    )
    dislikes_given = relationship(
        'Dislike',
        foreign_keys='Dislike.user_id',
        back_populates='user'
    )
    dislikes_received = relationship(
        'Dislike',
        foreign_keys='Dislike.target_user_id',
        back_populates='target_user'
    )
    
    # Отношение для рейтинга
    rating = relationship('Rating', back_populates='user', uselist=False, cascade='all, delete-orphan')


class User(BaseModel):
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="User's Telegram username with @ prefix")
    first_name: str = Field(..., description="User's first name")
    age: int = Field(..., description="User's age")
    gender: str = Field(..., description="User's gender")
    city_id: Optional[int] = Field(None, description="User's city ID") 