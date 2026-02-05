from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class Job(Base):
    """Background job tracking"""
    job_type = Column(String(64), nullable=False, index=True)  # retrain, export, backup, etc.
    status = Column(String(32), nullable=False, default="pending")  # pending, running, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    result_json = Column("result", JSON, nullable=True)  # Job result data
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(255), nullable=True)  # User ID
    metadata_json = Column("metadata", JSON, nullable=True)  # Job parameters

