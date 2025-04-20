from sqlalchemy import String, Integer, Column, ForeignKey, Text, Float, BigInteger
from .meta import Base

class Profile(Base):
    __tablename__ = "profiles"

    profile_id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True)
    bio = Column(Text)
    photo_url = Column(Text)
    preferred_gender = Column(String(10))
    preferred_age_min = Column(Integer)
    preferred_age_max = Column(Integer) 