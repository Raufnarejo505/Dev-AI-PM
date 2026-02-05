from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field, model_validator

from app.schemas.base import ORMBase


class AlarmCreate(BaseModel):
    machine_id: UUID
    sensor_id: Optional[UUID] = None
    prediction_id: Optional[UUID] = None
    severity: str
    message: str
    triggered_at: datetime
    metadata: Optional[dict] = Field(
        default=None,
        validation_alias=AliasChoices("metadata", "metadata_json"),
        serialization_alias="metadata",
    )


class AlarmUpdate(BaseModel):
    status: Optional[str] = None
    resolved_at: Optional[datetime] = None
    metadata: Optional[dict] = Field(
        default=None,
        validation_alias=AliasChoices("metadata", "metadata_json"),
        serialization_alias="metadata",
    )


class AlarmRead(ORMBase, AlarmCreate):
    status: str
    resolved_at: Optional[datetime] = None
    
    @model_validator(mode='before')
    @classmethod
    def extract_metadata(cls, data: Any) -> Any:
        """Extract metadata_json from SQLAlchemy model to avoid metadata conflict"""
        if not isinstance(data, dict) and hasattr(data, 'metadata_json'):
            # SQLAlchemy model - convert to dict and use metadata_json
            return {
                **{k: getattr(data, k, None) for k in ['id', 'created_at', 'updated_at', 
                    'machine_id', 'sensor_id', 'prediction_id', 'severity', 'message', 
                    'triggered_at', 'status', 'resolved_at']},
                'metadata_json': getattr(data, 'metadata_json', None),
            }
        return data

