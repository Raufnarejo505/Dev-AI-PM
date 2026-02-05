from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field

from app.schemas.base import ORMBase


class PredictionRequest(BaseModel):
    sensor_id: UUID
    machine_id: UUID
    timestamp: datetime
    value: float
    context: Optional[dict] = None


class PredictionCreate(BaseModel):
    sensor_id: UUID
    machine_id: UUID
    timestamp: datetime
    score: Optional[float] = None  # Keep for backward compatibility
    status: str = "normal"  # normal, warning, critical
    anomaly_type: Optional[str] = None
    model_version: Optional[str] = None
    remaining_useful_life: Optional[float] = None
    # New fields for AI contract
    prediction: Optional[str] = None  # String representation of prediction (e.g., "true", "false", "bearing_wear")
    confidence: Optional[float] = None  # Confidence score 0.0-1.0
    response_time_ms: Optional[float] = None  # Inference latency
    contributing_features: Optional[dict] = None  # Features that contributed to prediction
    metadata: Optional[dict] = Field(
        default=None,
        validation_alias=AliasChoices("metadata", "metadata_json"),
        serialization_alias="metadata",
    )

    model_config = {"protected_namespaces": ()}



class PredictionRead(ORMBase, PredictionCreate):
    pass


Prediction = PredictionRead


