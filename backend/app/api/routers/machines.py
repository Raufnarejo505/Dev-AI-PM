from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.api.dependencies import get_session, get_current_user, require_engineer
from app.schemas.machine import MachineCreate, MachineRead, MachineUpdate
from app.services import machine_service, prediction_service, sensor_data_service
from app.models.user import User
from app.models.sensor_data import SensorData
from app.models.prediction import Prediction
from app.models.alarm import Alarm

router = APIRouter(prefix="/machines", tags=["machines"])


@router.get("", response_model=List[MachineRead])
async def list_machines(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    machines = await machine_service.list_machines(session)
    # Convert SQLAlchemy models to Pydantic models
    result = []
    for m in machines:
        try:
            # Build dict with proper field mapping for MachineRead
            machine_dict = {
                "id": m.id,  # Keep as UUID
                "name": m.name,
                "location": m.location or "",
                "description": m.description or "",
                "status": m.status,
                "criticality": m.criticality,
                "metadata": getattr(m, 'metadata_json', None) or {},  # Map metadata_json to metadata
                "last_service_date": m.last_service_date,
                "created_at": m.created_at,
                "updated_at": m.updated_at,
            }
            # Validate and create MachineRead instance
            machine_read = MachineRead.model_validate(machine_dict)
            result.append(machine_read)
        except Exception as e:
            logger.error(f"Error serializing machine {m.id}: {e}")
            continue
    return result


@router.post("", response_model=MachineRead, status_code=status.HTTP_201_CREATED)
async def create_machine(payload: MachineCreate, session: AsyncSession = Depends(get_session)):
    return await machine_service.create_machine(session, payload)


@router.get("/{machine_id}", response_model=MachineRead)
async def get_machine(machine_id: UUID, session: AsyncSession = Depends(get_session)):
    machine = await machine_service.get_machine(session, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine


@router.patch("/{machine_id}", response_model=MachineRead)
async def update_machine(machine_id: UUID, payload: MachineUpdate, session: AsyncSession = Depends(get_session)):
    machine = await machine_service.get_machine(session, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return await machine_service.update_machine(session, machine, payload)


@router.delete("/{machine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_machine(machine_id: UUID, session: AsyncSession = Depends(get_session)):
    machine = await machine_service.get_machine(session, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    await machine_service.delete_machine(session, machine)


@router.post("/bulk", response_model=List[MachineRead], status_code=status.HTTP_201_CREATED)
async def create_machines_bulk(payload: List[MachineCreate], session: AsyncSession = Depends(get_session)):
    machines = []
    for machine_in in payload:
        machine = await machine_service.create_machine(session, machine_in)
        machines.append(machine)
    return machines


@router.get("/{machine_id}/summary")
async def get_machine_summary(
    machine_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get machine summary with last reading, last prediction, and active alarms"""
    machine = await machine_service.get_machine(session, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    # Get last sensor reading
    last_reading = await session.scalar(
        select(SensorData)
        .where(SensorData.machine_id == machine_id)
        .order_by(SensorData.timestamp.desc())
        .limit(1)
    )
    
    # Get last prediction
    last_prediction = await session.scalar(
        select(Prediction)
        .where(Prediction.machine_id == machine_id)
        .order_by(Prediction.timestamp.desc())
        .limit(1)
    )
    
    # Get active alarms
    active_alarms = await session.scalars(
        select(Alarm)
        .where(and_(Alarm.machine_id == machine_id, Alarm.status.in_(["open", "acknowledged"])))
        .order_by(Alarm.created_at.desc())
    )
    
    # Calculate uptime percentage (simplified - can be enhanced)
    total_readings = await session.scalar(
        select(func.count(SensorData.id)).where(SensorData.machine_id == machine_id)
    )
    active_alarms_list = list(active_alarms.scalars().all())
    
    return {
        "machine": {
            "id": str(machine.id),
            "name": machine.name,
            "status": machine.status,
            "criticality": machine.criticality,
            "ai": (machine.metadata_json or {}).get("ai_state") or {},
        },
        "lastReading": {
            "timestamp": last_reading.timestamp.isoformat() if last_reading else None,
            "value": float(last_reading.value) if last_reading else None,
            "sensor_id": str(last_reading.sensor_id) if last_reading else None,
        } if last_reading else None,
        "lastPrediction": {
            "timestamp": last_prediction.timestamp.isoformat() if last_prediction else None,
            "status": last_prediction.status if last_prediction else None,
            "confidence": float(last_prediction.confidence) if last_prediction and last_prediction.confidence else None,
            "model_version": last_prediction.model_version if last_prediction else None,
        } if last_prediction else None,
        "activeAlarms": len(active_alarms_list),
        "uptimePercent": 95.0 if machine.status == "online" else 0.0,  # Simplified calculation
    }


@router.patch("/{machine_id}/thresholds")
async def update_machine_thresholds(
    machine_id: UUID,
    thresholds: Dict[str, Any],
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_engineer),
):
    """Update machine thresholds (engineer/admin only)"""
    machine = await machine_service.get_machine(session, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    machine.thresholds_json = thresholds
    await session.commit()
    await session.refresh(machine)
    
    return {"machine_id": str(machine_id), "thresholds": thresholds}


@router.get("/{machine_id}/predictions")
async def get_machine_predictions(
    machine_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get predictions for a specific machine"""
    machine = await machine_service.get_machine(session, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    predictions = await prediction_service.get_history(
        session, str(machine_id), start_time, end_time, limit
    )
    return predictions


@router.get("/{machine_id}/sensor-data")
async def get_machine_sensor_data(
    machine_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    agg: str = Query("1m"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get sensor data for a specific machine"""
    machine = await machine_service.get_machine(session, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    start_time = datetime.fromisoformat(start) if start else None
    end_time = datetime.fromisoformat(end) if end else None
    
    # Query sensor data
    query = select(SensorData).where(SensorData.machine_id == machine_id)
    
    if start_time:
        query = query.where(SensorData.timestamp >= start_time)
    if end_time:
        query = query.where(SensorData.timestamp <= end_time)
    
    query = query.order_by(SensorData.timestamp.desc()).limit(limit)
    result = await session.execute(query)
    sensor_data_list = result.scalars().all()
    
    # Simple aggregation by time window if agg is specified
    # For now, return raw data - aggregation can be added later
    return [
        {
            "id": str(sd.id),
            "sensor_id": str(sd.sensor_id),
            "machine_id": str(sd.machine_id),
            "timestamp": sd.timestamp.isoformat(),
            "value": float(sd.value),
            "status": sd.status,
            "metadata": sd.metadata_json or {},
        }
        for sd in sensor_data_list
    ]

