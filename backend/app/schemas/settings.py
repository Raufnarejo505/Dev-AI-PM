from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import ORMBase


class SettingsCreate(BaseModel):
    key: str = Field(..., max_length=128)
    value: Optional[str] = None
    value_type: str = "string"  # string, number, boolean, json
    description: Optional[str] = None
    category: str = "general"
    is_public: bool = False
    metadata: Optional[Dict[str, Any]] = None


class SettingsUpdate(BaseModel):
    value: Optional[str] = None
    value_type: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_public: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class SettingsRead(ORMBase):
    key: str
    value: Optional[str] = None
    value_type: str
    description: Optional[str] = None
    category: str
    is_public: bool
    metadata: Optional[Dict[str, Any]] = None

