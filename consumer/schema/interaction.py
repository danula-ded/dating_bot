from pydantic import BaseModel


class InteractionMessage(BaseModel):
    """Schema for interaction messages (like/dislike/search)."""
    user_id: int
    action: str  # 'like', 'dislike', 'search'
    target_user_id: int | None = None 