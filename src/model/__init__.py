from sqlalchemy.orm import configure_mappers

from . import file
from .city import City
from .dislike import Dislike
from .file import FileRecord
from .interest import Interest
from .like import Like
from .meta import Base, metadata
from .profile import Profile
from .rating import Rating
from .user import User
from .user_interest import UserInterest

configure_mappers()

__all__ = [
    'Base',
    'metadata',
    'User',
    'City',
    'Interest',
    'UserInterest',
    'Profile',
    'Rating',
    'FileRecord',
    'Like',
    'Dislike',
]
