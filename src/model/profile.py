from sqlalchemy import BigInteger, Column, Float, ForeignKey, Integer, String, Text, Sequence

from .meta import Base


class Profile(Base):
    __tablename__ = "profiles"

    profile_id = Column(Integer, Sequence('profiles_profile_id_seq'), primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True)
    bio = Column(Text)
    photo_url = Column(Text)
    preferred_gender = Column(String(10))
    preferred_age_min = Column(Integer)
    preferred_age_max = Column(Integer)
