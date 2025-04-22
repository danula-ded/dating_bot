from pydantic import BaseModel

from .user import UserCreate
from .profile import ProfileCreate

 
class RegistrationMessage(BaseModel):
    user: UserCreate
    profile: ProfileCreate
    action: str = "user_registration" 