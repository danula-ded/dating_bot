from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .meta import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(64), unique=True)
    first_name = Column(String(64), nullable=False)
    age = Column(Integer)
    gender = Column(String(10))
    city_id = Column(Integer, ForeignKey("cities.city_id"))
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Define relationships explicitly
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
