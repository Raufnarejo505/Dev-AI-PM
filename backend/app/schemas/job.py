from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.base import ORMBase


class JobCreate(BaseModel):
    job_type: str  # retrain, export, backup, etc.
    metadata: Optional[Dict[str, Any]] = None


class JobUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class JobRead(ORMBase):
    job_type: str
    status: str
    progress: int
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

