from sqlalchemy import BigInteger, Column, Float, ForeignKey, Integer

from .meta import Base


class Rating(Base):
    __tablename__ = "ratings"

    rating_id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True)
    profile_score = Column(Float, default=0)
    activity_score = Column(Float, default=0)
