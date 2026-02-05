from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.base import ORMBase


class CommentCreate(BaseModel):
    resource_type: str  # alarm, ticket, etc.
    resource_id: str
    content: str
    is_internal: bool = False


class CommentRead(ORMBase):
    resource_type: str
    resource_id: str
    user_id: str
    content: str
    is_internal: bool

