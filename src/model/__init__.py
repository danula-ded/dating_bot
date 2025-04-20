from sqlalchemy.orm import configure_mappers

from . import file
from .meta import Base, metadata
from .user import User
from .city import City
from .interest import Interest
from .user_interest import UserInterest
from .profile import Profile
from .rating import Rating
from .file import FileRecord

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
]
