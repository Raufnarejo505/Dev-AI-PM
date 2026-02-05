from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class AuditLog(Base):
    """Audit log for tracking user actions and system events"""
    user_id = Column(String(255), nullable=True)  # Can be UUID or email
    action_type = Column(String(64), nullable=False)  # create, update, delete, login, prediction, alarm_resolve
    resource_type = Column(String(64), nullable=False)  # machine, sensor, prediction, alarm, user, etc.
    resource_id = Column(String(255), nullable=True)  # ID of the resource
    details = Column(Text, nullable=True)  # Human-readable description
    metadata_json = Column("metadata", JSON, nullable=True)  # Additional structured data
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(512), nullable=True)

