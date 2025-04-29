from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: Optional[str] = Field(None, max_length=64)
    first_name: str = Field(..., max_length=64)
    age: Optional[int] = Field(None, ge=18)
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    city_name: Optional[str] = Field(None, max_length=64)
    bio: Optional[str] = None
    photo_url: Optional[str] = None


class UserCreate(UserBase):
    user_id: int


class UserUpdate(UserBase):
    pass


class UserInDB(UserBase):
    user_id: int
    city_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
