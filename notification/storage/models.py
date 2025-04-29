"""Database models for notification service."""

from sqlalchemy import BigInteger, Column, Integer, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from notification.storage.db import Base


class City(Base):
    """City model for storing city information."""

    __tablename__ = 'cities'

    city_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    users = relationship('User', back_populates='city')


class User(Base):
    """User model for storing user information."""

    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(64), unique=True)
    first_name = Column(String(64), nullable=False)
    gender = Column(String(10))
    age = Column(Integer)
    city_id = Column(Integer, ForeignKey('cities.city_id'))
    created_at = Column(TIMESTAMP, server_default=func.now())

    profile = relationship('Profile', back_populates='user', uselist=False)
    city = relationship('City', back_populates='users')


class Profile(Base):
    """Profile model for storing user profile information."""

    __tablename__ = 'profiles'

    profile_id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), unique=True)
    bio = Column(Text)
    photo_url = Column(Text)
    preferred_gender = Column(String(10))
    preferred_age_min = Column(Integer)
    preferred_age_max = Column(Integer)

    user = relationship('User', back_populates='profile')
