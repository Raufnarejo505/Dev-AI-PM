from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ORMBase(BaseModel):
    id: Optional[UUID] = Field(default=None)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

