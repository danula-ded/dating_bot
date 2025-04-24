from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from consumer.model.meta import Base
from consumer.model.user import User

__all__ = ['Like', 'Dislike']


class Like(Base):
    """Модель для лайков."""
    __tablename__ = 'likes'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    target_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship(
        'User',
        foreign_keys=[user_id],
        back_populates='likes_given'
    )
    target_user = relationship(
        'User',
        foreign_keys=[target_user_id],
        back_populates='likes_received'
    )


class Dislike(Base):
    """Модель для дизлайков."""
    __tablename__ = 'dislikes'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    target_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship(
        'User',
        foreign_keys=[user_id],
        back_populates='dislikes_given'
    )
    target_user = relationship(
        'User',
        foreign_keys=[target_user_id],
        back_populates='dislikes_received'
    ) 