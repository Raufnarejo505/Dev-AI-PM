from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field, model_validator

from app.schemas.base import ORMBase


class TicketCreate(BaseModel):
    machine_id: UUID
    alarm_id: Optional[UUID] = None
    title: str
    priority: str = "medium"
    assignee: Optional[str] = None
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    auto_created: bool = True
    metadata: Optional[dict] = Field(
        default=None,
        validation_alias=AliasChoices("metadata", "metadata_json"),
        serialization_alias="metadata",
    )


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    assignee: Optional[str] = None
    resolution_notes: Optional[str] = None
    due_at: Optional[datetime] = None
    metadata: Optional[dict] = Field(
        default=None,
        validation_alias=AliasChoices("metadata", "metadata_json"),
        serialization_alias="metadata",
    )


class TicketRead(ORMBase, TicketCreate):
    status: str
    
    @model_validator(mode='before')
    @classmethod
    def extract_metadata(cls, data: Any) -> Any:
        """Extract metadata_json from SQLAlchemy model to avoid metadata conflict"""
        if not isinstance(data, dict) and hasattr(data, 'metadata_json'):
            # SQLAlchemy model - convert to dict and use metadata_json
            return {
                **{k: getattr(data, k, None) for k in ['id', 'created_at', 'updated_at',
                    'machine_id', 'alarm_id', 'title', 'priority', 'assignee', 
                    'description', 'due_at', 'auto_created', 'status']},
                'metadata_json': getattr(data, 'metadata_json', None),
            }
        return data

