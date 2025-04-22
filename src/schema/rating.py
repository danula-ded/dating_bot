from pydantic import BaseModel, Field


class RatingBase(BaseModel):
    profile_score: float = Field(0, ge=0, le=10)
    activity_score: float = Field(0, ge=0, le=10)


class RatingCreate(RatingBase):
    user_id: int


class RatingUpdate(RatingBase):
    pass


class RatingInDB(RatingBase):
    rating_id: int
    user_id: int

    class Config:
        from_attributes = True
