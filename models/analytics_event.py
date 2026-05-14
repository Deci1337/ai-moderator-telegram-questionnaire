from sqlalchemy import Column, BigInteger, Integer, String, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from config.database import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    __table_args__ = (
        Index("ix_analytics_events_event_type_created_at", "event_type", "created_at"),
        Index("ix_analytics_events_session_id", "session_id"),
        Index("ix_analytics_events_user_id", "user_id"),
        {"schema": "pride_academy"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(64), nullable=False)
    user_id = Column(BigInteger, nullable=True)
    target_id = Column(BigInteger, nullable=True)
    session_id = Column(String(64), nullable=True)
    payload = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
