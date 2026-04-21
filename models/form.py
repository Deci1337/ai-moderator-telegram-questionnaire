from sqlalchemy import Column, BigInteger, Integer, String, text
from config.database import Base


class Form(Base):
    __tablename__ = "forms"
    __table_args__ = {"schema": "pride_academy"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, unique=True)
    cups = Column(BigInteger)
    photo_id = Column(String)
    description = Column(String)
    searchs = Column(String)
    tier = Column(String(1))
    rank = Column(String)
    league_rank = Column(Integer)
    timestamp = Column(String, server_default=text("now()"), nullable=False)
