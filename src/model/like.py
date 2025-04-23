from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from src.model import meta


class Like(meta.Base):
    """Модель для хранения лайков между пользователями."""
    __tablename__ = 'likes'

    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    to_user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)

    # Отношения для удобного доступа к данным пользователей
    from_user = relationship('User', foreign_keys=[user_id], back_populates='likes_given')
    to_user = relationship('User', foreign_keys=[to_user_id], back_populates='likes_received') 