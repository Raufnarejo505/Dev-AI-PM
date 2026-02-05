from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field


class SensorDataIn(BaseModel):
    sensor_id: UUID
    machine_id: UUID
    timestamp: datetime
    value: float
    status: str = "normal"
    metadata: Optional[dict] = Field(
        default=None,
        validation_alias=AliasChoices("metadata", "metadata_json"),
        serialization_alias="metadata",
    )



class SensorDataOut(SensorDataIn):
    id: int

    model_config = {"from_attributes": True}


SensorData = SensorDataOut

