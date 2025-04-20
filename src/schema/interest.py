from pydantic import BaseModel, Field

class InterestBase(BaseModel):
    name: str = Field(..., max_length=64)

class InterestCreate(InterestBase):
    pass

class InterestInDB(InterestBase):
    interest_id: int

    class Config:
        from_attributes = True 