from pydantic import BaseModel

from .profile import ProfileCreate
from .user import UserCreate


class RegistrationMessage(BaseModel):
    user: UserCreate
    profile: ProfileCreate
    action: str = "user_registration"
