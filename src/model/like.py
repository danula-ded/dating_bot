from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from .meta import Base


class Like(Base):
    """Модель для лайков."""
    __tablename__ = 'likes'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    target_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Define relationships with back_populates
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