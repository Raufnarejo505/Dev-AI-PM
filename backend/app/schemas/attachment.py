from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.base import ORMBase


class AttachmentCreate(BaseModel):
    resource_type: str  # alarm, ticket, report, etc.
    resource_id: Optional[str] = None
    filename: Optional[str] = None
    content_type: Optional[str] = None


class AttachmentRead(ORMBase):
    filename: str
    file_path: str
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    resource_type: str
    resource_id: Optional[str] = None
    uploaded_by: Optional[str] = None

