from pydantic import BaseModel


class DislikeBase(BaseModel):
    """Базовая схема для дизлайка."""
    user_id: int
    to_user_id: int


class DislikeCreate(DislikeBase):
    """Схема для создания дизлайка."""
    pass


class DislikeRead(DislikeBase):
    """Схема для чтения дизлайка."""
    pass


class DislikeInDB(DislikeBase):
    """Схема для дизлайка в БД."""
    class Config:
        from_attributes = True 