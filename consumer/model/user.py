from typing import Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="User's Telegram username with @ prefix")
    first_name: str = Field(..., description="User's first name")
    age: int = Field(..., description="User's age")
    gender: str = Field(..., description="User's gender")
    city_id: Optional[int] = Field(None, description="User's city ID") 