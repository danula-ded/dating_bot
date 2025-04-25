from sqlalchemy import Column, Integer, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from consumer.model.meta import Base


class Rating(Base):
    """Модель для рейтинга пользователя."""

    __tablename__ = 'ratings'

    rating_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), unique=True, nullable=False)
    profile_score = Column(Float, default=5.0, nullable=False)
    activity_score = Column(Float, default=0.0, nullable=False)

    # Relationship with User
    user = relationship('User', back_populates='rating')

    # Add check constraints
    __table_args__ = (
        CheckConstraint('profile_score >= 0 AND profile_score <= 10', name='check_profile_score_range'),
        CheckConstraint('activity_score >= 0 AND activity_score <= 10', name='check_activity_score_range'),
    )
