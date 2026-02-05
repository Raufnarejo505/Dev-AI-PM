from sqlalchemy import Column, JSON, String, Text

from app.models.base import Base


class ModelRegistry(Base):
    name = Column(String(128), nullable=False)
    version = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)
    path = Column(String(255), nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)

