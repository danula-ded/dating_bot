from typing import Optional
from pydantic import BaseModel, Field


class Profile(BaseModel):
    id: int = Field(..., description="Profile ID")
    bio: Optional[str] = Field(None, description="User's bio")
    photo_url: Optional[str] = Field(None, description="URL to user's photo")
    preferred_gender: Optional[str] = Field(None, description="Preferred gender for matches")
    preferred_age_min: Optional[int] = Field(None, description="Minimum preferred age")
    preferred_age_max: Optional[int] = Field(None, description="Maximum preferred age") 