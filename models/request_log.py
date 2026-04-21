from sqlalchemy import Column, Integer, String, text
from config.database import Base


class RequestLog(Base):
    __tablename__ = "request_logs"
    __table_args__ = {"schema": "pride_academy"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    method = Column(String(10), nullable=False)
    path = Column(String(255), nullable=False)
    ip = Column(String(45), nullable=False)
    timestamp = Column(String, server_default=text("now()"), nullable=False)
