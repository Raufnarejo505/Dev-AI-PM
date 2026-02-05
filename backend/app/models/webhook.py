from sqlalchemy import Column, Boolean, JSON, String, Text

from app.models.base import Base


class Webhook(Base):
    """Webhook configuration for external integrations"""
    name = Column(String(128), nullable=False)
    url = Column(Text, nullable=False)
    secret = Column(String(255), nullable=True)  # For HMAC signature
    events = Column(JSON, nullable=False)  # List of event types: ["alarm.created", "prediction.critical", etc.]
    is_active = Column(Boolean, default=True)
    headers = Column(JSON, nullable=True)  # Custom headers to include
    timeout_seconds = Column(String(32), default="5")  # Request timeout
    retry_count = Column(String(32), default="3")  # Number of retries
    metadata_json = Column("metadata", JSON, nullable=True)

