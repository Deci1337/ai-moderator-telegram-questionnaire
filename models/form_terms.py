from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from config.database import Base


class FormTerms(Base):
    __tablename__ = "form_terms"
    __table_args__ = {"schema": "pride_academy"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    form_id = Column(Integer, ForeignKey("pride_academy.forms.id", ondelete="CASCADE"), nullable=False)
    expiry_date = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
