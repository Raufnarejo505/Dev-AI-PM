from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.base import ORMBase


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = []  # List of permission strings


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class RoleRead(ORMBase):
    name: str
    description: Optional[str] = None
    permissions: List[str]
    is_system: bool = False


class PermissionUpdate(BaseModel):
    permissions: List[str]

