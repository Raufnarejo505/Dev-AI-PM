from sqlalchemy import Column, DateTime, String

from app.models.base import Base


class User(Base):
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    role = Column(String(64), nullable=False, default="operator")
    hashed_password = Column(String(255), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    refresh_token_hash = Column(String(255), nullable=True)
    refresh_token_expires_at = Column(DateTime(timezone=True), nullable=True)

