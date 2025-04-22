from typing import Optional

from pydantic import BaseModel, Field


class ProfileBase(BaseModel):
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    preferred_gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    preferred_age_min: Optional[int] = Field(None, ge=18)
    preferred_age_max: Optional[int] = Field(None, ge=18)


class ProfileCreate(ProfileBase):
    user_id: int


class ProfileUpdate(ProfileBase):
    pass


class ProfileInDB(ProfileBase):
    profile_id: int
    user_id: int

    class Config:
        from_attributes = True
