from sqlalchemy import Column, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class Attachment(Base):
    """File attachments for tickets, alarms, reports"""
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)  # Storage path
    content_type = Column(String(128), nullable=True)  # MIME type
    file_size = Column(Integer, nullable=True)  # Size in bytes
    resource_type = Column(String(64), nullable=False)  # alarm, ticket, report, etc.
    resource_id = Column(String(255), nullable=True)  # ID of the resource
    uploaded_by = Column(String(255), nullable=True)  # User ID
    metadata_json = Column("metadata", JSON, nullable=True)  # Additional metadata

