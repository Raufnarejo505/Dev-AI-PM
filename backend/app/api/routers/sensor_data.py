from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_current_user, require_viewer
from app.models.user import User
from app.schemas.sensor_data import SensorDataIn, SensorDataOut
from app.services import alarm_service, sensor_data_service, sensor_service
from app.models.sensor_data import SensorData

router = APIRouter(prefix="/sensor-data", tags=["sensor_data"])


@router.post("", response_model=SensorDataOut, status_code=status.HTTP_201_CREATED)
async def ingest_sensor_data(payload: SensorDataIn, session: AsyncSession = Depends(get_session)):
    sensor_data = await sensor_data_service.ingest_sensor_data(session, payload)
    sensor = await sensor_service.get_sensor(session, payload.sensor_id)
    if sensor:
        await alarm_service.auto_alarm_from_sensor_value(
            session=session,
            sensor=sensor,
            machine_id=payload.machine_id,
            value=payload.value,
            timestamp=payload.timestamp,
        )
    return sensor_data


@router.get("", response_model=List[SensorDataOut])
async def get_sensor_data(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_viewer),
    sensor_id: Optional[UUID] = Query(None),
    machine_id: Optional[UUID] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort: str = Query("desc", regex="^(asc|desc)$"),
):
    """Get sensor data with filtering - supports both /sensor-data and /sensor-data/logs"""
    from loguru import logger
    from app.models.sensor import Sensor
    
    # Build query without relationships first
    conditions = []
    if sensor_id:
        conditions.append(SensorData.sensor_id == sensor_id)
    if machine_id:
        conditions.append(SensorData.machine_id == machine_id)
    if start_date:
        conditions.append(SensorData.timestamp >= start_date)
    if end_date:
        conditions.append(SensorData.timestamp <= end_date)
    
    # Select only actual columns that exist in the database
    # Note: readings and raw_payload columns don't exist in DB, so we exclude them
    query = select(
        SensorData.id,
        SensorData.sensor_id,
        SensorData.machine_id,
        SensorData.timestamp,
        SensorData.value,
        SensorData.status,
        SensorData.metadata_json,
        SensorData.idempotency_key,
        SensorData.created_at,
        SensorData.updated_at
    )
    if conditions:
        query = query.where(and_(*conditions))
    
    # Apply sorting
    if sort == "desc":
        query = query.order_by(SensorData.timestamp.desc())
    else:
        query = query.order_by(SensorData.timestamp.asc())
    
    query = query.limit(limit).offset(offset)
    result = await session.execute(query)
    rows = result.all()
    
    # Convert rows to objects with attributes
    class SensorDataRow:
        def __init__(self, row):
            self.id = row.id
            self.sensor_id = row.sensor_id
            self.machine_id = row.machine_id
            self.timestamp = row.timestamp
            self.value = row.value
            self.status = row.status
            self.metadata_json = row.metadata_json
            self.idempotency_key = row.idempotency_key
            self.created_at = row.created_at
            self.updated_at = row.updated_at
    
    sensor_data_list = [SensorDataRow(row) for row in rows]
    
    # Fetch sensors separately if we have sensor IDs
    sensor_ids = list(set([sd.sensor_id for sd in sensor_data_list]))
    sensors_dict = {}
    if sensor_ids:
        sensors_query = select(Sensor).where(Sensor.id.in_(sensor_ids))
        sensors_result = await session.execute(sensors_query)
        sensors_list = sensors_result.scalars().all()
        sensors_dict = {s.id: s for s in sensors_list}
    
    # Manually serialize to avoid relationship serialization issues
    # Include sensor and machine info in metadata for frontend
    serialized = []
    for sd in sensor_data_list:
        try:
            # Get metadata safely - handle both dict and JSON string
            metadata = {}
            if sd.metadata_json:
                if isinstance(sd.metadata_json, dict):
                    metadata = dict(sd.metadata_json)  # Create a copy
                elif isinstance(sd.metadata_json, str):
                    import json
                    try:
                        metadata = json.loads(sd.metadata_json)
                    except json.JSONDecodeError:
                        metadata = {}
                else:
                    metadata = {}
            
            # Add sensor info to metadata from our fetched sensors dict
            sensor = sensors_dict.get(sd.sensor_id)
            if sensor:
                metadata['sensor_name'] = str(sensor.name) if sensor.name else ""
                metadata['sensor_type'] = str(sensor.sensor_type) if sensor.sensor_type else ""
                metadata['sensor_unit'] = str(sensor.unit) if sensor.unit else ""
                # Safely merge sensor metadata
                if sensor.metadata_json:
                    if isinstance(sensor.metadata_json, dict):
                        metadata.update(sensor.metadata_json)
                    elif isinstance(sensor.metadata_json, str):
                        import json
                        try:
                            sensor_meta_dict = json.loads(sensor.metadata_json)
                            if isinstance(sensor_meta_dict, dict):
                                metadata.update(sensor_meta_dict)
                        except (json.JSONDecodeError, TypeError):
                            pass
            
            # Ensure value is a float
            value = 0.0
            if sd.value is not None:
                try:
                    value = float(sd.value)
                except (ValueError, TypeError):
                    value = 0.0
            
            # Create the response object
            serialized.append(SensorDataOut(
                id=sd.id,
                sensor_id=sd.sensor_id,
                machine_id=sd.machine_id,
                timestamp=sd.timestamp,
                value=value,
                status=sd.status or "normal",
                metadata=metadata if metadata else None,
            ))
        except Exception as e:
            # Log error but continue with other records
            logger.error(f"Error serializing sensor data {sd.id}: {e}", exc_info=True)
            # Create a minimal valid response as fallback
            try:
                value = 0.0
                if sd.value is not None:
                    try:
                        value = float(sd.value)
                    except (ValueError, TypeError):
                        value = 0.0
                
                serialized.append(SensorDataOut(
                    id=sd.id,
                    sensor_id=sd.sensor_id,
                    machine_id=sd.machine_id,
                    timestamp=sd.timestamp,
                    value=value,
                    status=getattr(sd, 'status', 'normal') or "normal",
                    metadata=sd.metadata_json if hasattr(sd, 'metadata_json') and sd.metadata_json else None,
                ))
            except Exception as fallback_err:
                logger.error(f"Fallback serialization also failed for sensor_data {sd.id}: {fallback_err}")
                # Skip this record if we can't serialize it at all
                continue
    
    return serialized


@router.get("/logs", response_model=List[SensorDataOut])
async def get_sensor_data_logs(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_viewer),
    sensor_id: Optional[UUID] = Query(None),
    machine_id: Optional[UUID] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get sensor data logs with filtering - alias for /sensor-data"""
    return await get_sensor_data(
        session=session,
        current_user=current_user,
        sensor_id=sensor_id,
        machine_id=machine_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
        sort="desc"
    )

