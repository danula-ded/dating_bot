from typing import Optional
from pydantic import BaseModel


class ProfileSearchRequest(BaseModel):
    """Схема запроса для поиска анкет."""

    user_id: int
    age_from: Optional[int] = None
    age_to: Optional[int] = None
    gender: Optional[str] = None


class ProfileSearchResponse(BaseModel):
    """Схема ответа с данными анкеты для просмотра."""

    user_id: int
    first_name: str
    age: int
    gender: str
    bio: Optional[str]
    photo_url: Optional[str]
