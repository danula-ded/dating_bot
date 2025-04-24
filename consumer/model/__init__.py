from sqlalchemy.orm import configure_mappers

from . import file
from .user import User
from .profile import Profile
from .interaction import Like, Dislike

configure_mappers()

__all__ = ['User', 'Profile', 'Like', 'Dislike']
