from sqlalchemy import Column, Boolean, JSON, Numeric, String, Text

from app.models.base import Base


class Settings(Base):
    """System-wide settings and configuration"""
    key = Column(String(128), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)  # JSON string or plain text
    value_type = Column(String(32), nullable=False, default="string")  # string, number, boolean, json
    description = Column(Text, nullable=True)
    category = Column(String(64), nullable=False, default="general")  # general, thresholds, notifications, ai, etc.
    is_public = Column(Boolean, default=False)  # Whether frontend can read this setting
    metadata_json = Column("metadata", JSON, nullable=True)

