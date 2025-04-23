from sqlalchemy.orm import configure_mappers

from . import file
from .user import User
from .profile import Profile

configure_mappers()

__all__ = ['User', 'Profile']
