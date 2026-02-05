from sqlalchemy import Column, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class Comment(Base):
    """Comments on alarms, tickets, or other resources"""
    resource_type = Column(String(64), nullable=False)  # alarm, ticket, etc.
    resource_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False)  # User who created comment
    content = Column(Text, nullable=False)
    is_internal = Column(String(32), default="false")  # Internal comments not visible to all users
    metadata_json = Column("metadata", JSON, nullable=True)

