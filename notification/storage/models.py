"""Database models for notification service."""
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from notification.storage.db import Base


class User(Base):
    """User model."""
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[str] = mapped_column(String(50), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(255), nullable=True) 