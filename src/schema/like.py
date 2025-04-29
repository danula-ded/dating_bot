from pydantic import BaseModel


class LikeBase(BaseModel):
    """Базовая схема для лайка."""

    user_id: int
    to_user_id: int


class LikeCreate(LikeBase):
    """Схема для создания лайка."""

    pass


class LikeRead(LikeBase):
    """Схема для чтения лайка."""

    pass


class LikeInDB(LikeBase):
    """Схема для лайка в БД."""

    class Config:
        from_attributes = True
