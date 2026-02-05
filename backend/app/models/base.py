from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.sql import func
from sqlalchemy import DateTime, Uuid, Column


class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:  # type: ignore
        return cls.__name__.lower()

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

