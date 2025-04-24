from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from consumer.model.meta import Base


class User(Base):
    """Модель пользователя."""
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

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


class User(BaseModel):
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="User's Telegram username with @ prefix")
    first_name: str = Field(..., description="User's first name")
    age: int = Field(..., description="User's age")
    gender: str = Field(..., description="User's gender")
    city_id: Optional[int] = Field(None, description="User's city ID") 