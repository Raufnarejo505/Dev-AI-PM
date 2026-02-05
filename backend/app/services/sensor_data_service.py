from datetime import datetime
from typing import List

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sensor_data import SensorData
from app.schemas.sensor_data import SensorDataIn


def _prepare_payload(data: dict) -> dict:
    metadata = data.pop("metadata", None)
    if metadata is not None:
        data["metadata_json"] = metadata
    return data


async def ingest_sensor_data(session: AsyncSession, payload: SensorDataIn) -> SensorData:
    # Create SensorData directly from payload, ensuring UUIDs stay as UUID objects
    # Don't use model_dump() as it converts UUIDs to strings
    sensor_data = SensorData(
        sensor_id=payload.sensor_id,  # Keep as UUID object
        machine_id=payload.machine_id,  # Keep as UUID object
        timestamp=payload.timestamp,
        value=payload.value,
        status=payload.status,
        metadata_json=payload.metadata,  # Map metadata to metadata_json
    )
    session.add(sensor_data)
    await session.commit()
    # Refresh only specific columns to avoid issues with missing columns
    await session.refresh(sensor_data, ["id", "created_at", "updated_at"])
    
    # Broadcast real-time update for dashboard
    try:
        from app.api.routers.realtime import broadcast_update
        from loguru import logger
        await broadcast_update(
            "sensor_data.created",
            {
                "id": sensor_data.id,
                "sensor_id": str(sensor_data.sensor_id),
                "machine_id": str(sensor_data.machine_id),
                "value": float(sensor_data.value) if sensor_data.value else 0.0,
                "status": sensor_data.status or "normal",
                "timestamp": sensor_data.timestamp.isoformat() if sensor_data.timestamp else None,
                "metadata": sensor_data.metadata_json,
            }
        )
    except Exception as e:
        # Use logger if available, otherwise silent fail
        try:
            from loguru import logger
            logger.debug(f"Failed to broadcast sensor data update: {e}")
        except:
            pass
    
    return sensor_data


async def bulk_ingest(session: AsyncSession, rows: List[SensorDataIn]) -> None:
    if not rows:
        return
    values = [_prepare_payload(row.model_dump()) for row in rows]
    await session.execute(insert(SensorData), values)
    await session.commit()


async def recent_sensor_data(
    session: AsyncSession,
    sensor_id: str,
    limit: int = 100,
):
    stmt = (
        select(SensorData)
        .where(SensorData.sensor_id == sensor_id)
        .order_by(SensorData.timestamp.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(reversed(result.scalars().all()))


async def get_history(
    session: AsyncSession,
    machine_id: str,
    start_time: datetime = None,
    end_time: datetime = None,
    limit: int = 1000,
) -> List[SensorData]:
    stmt = select(SensorData).where(SensorData.machine_id == machine_id)
    
    if start_time:
        stmt = stmt.where(SensorData.timestamp >= start_time)
    if end_time:
        stmt = stmt.where(SensorData.timestamp <= end_time)
        
    stmt = stmt.order_by(SensorData.timestamp.desc()).limit(limit)
    
    result = await session.execute(stmt)
    return list(reversed(result.scalars().all()))

