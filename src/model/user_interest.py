from sqlalchemy import BigInteger, Column, ForeignKey, Integer

from .meta import Base


class UserInterest(Base):
    __tablename__ = "user_interests"

    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    interest_id = Column(Integer, ForeignKey("interests.interest_id", ondelete="CASCADE"), primary_key=True)
