from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from src.model import meta


class Dislike(meta.Base):
    """Модель для хранения дизлайков между пользователями."""
    __tablename__ = 'dislikes'

    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    to_user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)

    # Отношения для удобного доступа к данным пользователей
    from_user = relationship('User', foreign_keys=[user_id], back_populates='dislikes_given')
    to_user = relationship('User', foreign_keys=[to_user_id], back_populates='dislikes_received') 