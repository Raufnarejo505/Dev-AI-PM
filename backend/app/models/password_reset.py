from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class PasswordResetToken(Base):
    """Password reset token storage"""
    user_id = Column(String(255), nullable=False, index=True)  # Can be UUID string or email
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(String(32), default="false")  # "true" or "false" as string for simplicity
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)

