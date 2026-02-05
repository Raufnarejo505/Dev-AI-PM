from sqlalchemy import Column, JSON, String

from app.models.base import Base


class Role(Base):
    """Role definition with permissions"""
    name = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(String(512), nullable=True)
    permissions_json = Column("permissions", JSON, nullable=False, default=list)  # List of permission strings
    is_system = Column(String(32), default="false")  # System roles can't be deleted

