from sqlalchemy.orm import configure_mappers

from . import file
<<<<<<< HEAD
from .user import User
from .profile import Profile
from .interaction import Like, Dislike
from .rating import Rating

configure_mappers()

__all__ = ['User', 'Profile', 'Like', 'Dislike', 'Rating']
=======

configure_mappers()
>>>>>>> main
