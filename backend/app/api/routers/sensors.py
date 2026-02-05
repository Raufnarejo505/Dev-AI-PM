from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_current_user
from app.models.user import User
from app.schemas.sensor import SensorCreate, SensorRead, SensorUpdate
from app.services import sensor_service
from app.models.sensor_data import SensorData

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.get("", response_model=List[SensorRead])
async def list_sensors(
    machine_id: Optional[UUID] = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    sensors = await sensor_service.list_sensors(session, machine_id)

    # Manually construct response to avoid SQLAlchemy metadata serialization issues.
    result: List[SensorRead] = []
    for sensor in sensors:
        result.append(
            SensorRead(
                id=sensor.id,
                machine_id=sensor.machine_id,
                name=sensor.name,
                sensor_type=sensor.sensor_type,
                unit=sensor.unit,
                min_threshold=float(sensor.min_threshold) if sensor.min_threshold is not None else None,
                max_threshold=float(sensor.max_threshold) if sensor.max_threshold is not None else None,
                warning_threshold=float(sensor.warning_threshold) if sensor.warning_threshold is not None else None,
                critical_threshold=float(sensor.critical_threshold) if sensor.critical_threshold is not None else None,
                metadata=sensor.metadata_json,
                created_at=sensor.created_at,
                updated_at=sensor.updated_at,
            )
        )
    return result


@router.post("", response_model=SensorRead, status_code=status.HTTP_201_CREATED)
async def create_sensor(payload: SensorCreate, session: AsyncSession = Depends(get_session)):
    sensor = await sensor_service.create_sensor(session, payload)
    # Manually construct response dict to avoid SQLAlchemy metadata conflict
    sensor_dict = {
        "id": sensor.id,
        "machine_id": sensor.machine_id,
        "name": sensor.name,
        "sensor_type": sensor.sensor_type,
        "unit": sensor.unit,
        "min_threshold": float(sensor.min_threshold) if sensor.min_threshold is not None else None,
        "max_threshold": float(sensor.max_threshold) if sensor.max_threshold is not None else None,
        "warning_threshold": float(sensor.warning_threshold) if sensor.warning_threshold is not None else None,
        "critical_threshold": float(sensor.critical_threshold) if sensor.critical_threshold is not None else None,
        "metadata": sensor.metadata_json,  # Map metadata_json to metadata
        "created_at": sensor.created_at,
        "updated_at": sensor.updated_at,
    }
    return SensorRead(**sensor_dict)


@router.get("/{sensor_id}", response_model=SensorRead)
async def get_sensor(sensor_id: UUID, session: AsyncSession = Depends(get_session)):
    sensor = await sensor_service.get_sensor(session, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    # Manually construct response to avoid metadata serialization issues
    return SensorRead(
        id=sensor.id,
        machine_id=sensor.machine_id,
        name=sensor.name,
        sensor_type=sensor.sensor_type,
        unit=sensor.unit,
        min_threshold=float(sensor.min_threshold) if sensor.min_threshold is not None else None,
        max_threshold=float(sensor.max_threshold) if sensor.max_threshold is not None else None,
        warning_threshold=float(sensor.warning_threshold) if sensor.warning_threshold is not None else None,
        critical_threshold=float(sensor.critical_threshold) if sensor.critical_threshold is not None else None,
        metadata=sensor.metadata_json,
        created_at=sensor.created_at,
        updated_at=sensor.updated_at,
    )


@router.patch("/{sensor_id}", response_model=SensorRead)
async def update_sensor(sensor_id: UUID, payload: SensorUpdate, session: AsyncSession = Depends(get_session)):
    sensor = await sensor_service.get_sensor(session, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return await sensor_service.update_sensor(session, sensor, payload)


@router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sensor(sensor_id: UUID, session: AsyncSession = Depends(get_session)):
    sensor = await sensor_service.get_sensor(session, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    await sensor_service.delete_sensor(session, sensor)


@router.get("/{sensor_id}/trend")
async def get_sensor_trend(
    sensor_id: UUID,
    interval: str = Query("24h", regex="^(1h|6h|24h|7d|30d)$"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get sensor trend data for the specified interval"""
    sensor = await sensor_service.get_sensor(session, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    # Parse interval
    interval_map = {
        "1h": timedelta(hours=1),
        "6h": timedelta(hours=6),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
    }
    delta = interval_map.get(interval, timedelta(hours=24))
    since = datetime.utcnow() - delta
    
    # Get sensor data points
    data_points = await session.scalars(
        select(SensorData)
        .where(and_(SensorData.sensor_id == sensor_id, SensorData.timestamp >= since))
        .order_by(SensorData.timestamp.asc())
    )
    
    points = [
        {
            "timestamp": point.timestamp.isoformat(),
            "value": float(point.value),
            "status": point.status,
        }
        for point in data_points
    ]
    
    # Calculate statistics
    if points:
        values = [p["value"] for p in points]
        return {
            "sensor_id": str(sensor_id),
            "interval": interval,
            "points": points,
            "statistics": {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
            },
        }
    else:
        return {
            "sensor_id": str(sensor_id),
            "interval": interval,
            "points": [],
            "statistics": None,
        }

