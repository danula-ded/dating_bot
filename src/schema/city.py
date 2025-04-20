from pydantic import BaseModel, Field

class CityBase(BaseModel):
    name: str = Field(..., max_length=64)

class CityCreate(CityBase):
    pass

class CityInDB(CityBase):
    city_id: int

    class Config:
        from_attributes = True 