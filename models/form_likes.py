from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func
from config.database import Base


class FormLikes(Base):
    __tablename__ = "form_likes"
    __table_args__ = (
        UniqueConstraint('user_id', 'liked_user_id', 'form_id', name='uq_user_form_like'),
        {"schema": "pride_academy"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    form_id = Column(Integer, ForeignKey("pride_academy.forms.id", ondelete="CASCADE"), nullable=False)
    liked_user_id = Column(BigInteger, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
