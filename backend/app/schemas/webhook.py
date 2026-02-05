from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import ORMBase


class WebhookCreate(BaseModel):
    name: str = Field(..., max_length=128)
    url: str
    secret: Optional[str] = None
    events: List[str] = Field(..., description="List of event types, e.g., ['alarm.created', 'prediction.critical']")
    is_active: bool = True
    headers: Optional[Dict[str, str]] = None
    timeout_seconds: str = "5"
    retry_count: str = "3"
    metadata: Optional[Dict[str, Any]] = None


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    secret: Optional[str] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None
    headers: Optional[Dict[str, str]] = None
    timeout_seconds: Optional[str] = None
    retry_count: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class WebhookRead(ORMBase):
    name: str
    url: str
    secret: Optional[str] = None
    events: List[str]
    is_active: bool
    headers: Optional[Dict[str, str]] = None
    timeout_seconds: str
    retry_count: str
    metadata: Optional[Dict[str, Any]] = None

