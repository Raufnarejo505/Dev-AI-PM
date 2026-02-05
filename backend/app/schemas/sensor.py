from typing import Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field, field_serializer, model_validator

from app.schemas.base import ORMBase


class SensorBase(BaseModel):
    machine_id: UUID
    name: str
    sensor_type: str
    unit: Optional[str] = None
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    metadata: Optional[dict] = Field(
        default=None,
        validation_alias=AliasChoices("metadata", "metadata_json"),
        serialization_alias="metadata",
    )


class SensorCreate(SensorBase):
    pass


class SensorUpdate(BaseModel):
    name: Optional[str] = None
    sensor_type: Optional[str] = None
    unit: Optional[str] = None
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    metadata: Optional[dict] = Field(
        default=None,
        validation_alias=AliasChoices("metadata", "metadata_json"),
        serialization_alias="metadata",
    )


class SensorRead(ORMBase, SensorBase):
    id: UUID
    
    model_config = {
        "from_attributes": False,  # Disable to avoid SQLAlchemy metadata conflict
        "populate_by_name": True,
    }

