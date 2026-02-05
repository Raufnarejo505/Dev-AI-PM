from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field

from app.schemas.base import ORMBase


class MachineBase(BaseModel):
    name: str
    location: Optional[str] = None
    description: Optional[str] = None
    status: str = Field(default="online")
    criticality: str = Field(default="medium")
    metadata: Optional[dict] = Field(
        default=None,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    last_service_date: Optional[date] = None


class MachineCreate(MachineBase):
    pass


class MachineUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    criticality: Optional[str] = None
    metadata: Optional[dict] = Field(
        default=None,
        validation_alias=AliasChoices("metadata", "metadata_json"),
        serialization_alias="metadata",
    )
    last_service_date: Optional[date] = None


class MachineRead(ORMBase, MachineBase):
    id: UUID
    
    model_config = {
        "from_attributes": False,  # Disabled to avoid SQLAlchemy metadata conflict
        "populate_by_name": True,
    }

