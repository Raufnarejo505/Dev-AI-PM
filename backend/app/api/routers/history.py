from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_current_user
from app.schemas.sensor_data import SensorData as SensorDataSchema
from app.schemas.prediction import Prediction as PredictionSchema
from app.services import sensor_data_service, prediction_service
from app.models.user import User

router = APIRouter(tags=["history"])


@router.get("/machines/{machine_id}/sensor-data", response_model=List[SensorDataSchema])
async def get_machine_sensor_data(
    machine_id: UUID,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Get historical sensor data for a machine.
    """
    return await sensor_data_service.get_history(
        session, str(machine_id), start_time, end_time, limit
    )


@router.get("/machines/{machine_id}/predictions", response_model=List[PredictionSchema])
async def get_machine_predictions(
    machine_id: UUID,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Get historical predictions for a machine.
    """
    return await prediction_service.get_history(
        session, str(machine_id), start_time, end_time, limit
    )
