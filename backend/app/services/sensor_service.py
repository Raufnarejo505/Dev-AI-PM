from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sensor import Sensor
from app.schemas.sensor import SensorCreate, SensorUpdate


def _prepare_payload(data: dict) -> dict:
    metadata = data.pop("metadata", None)
    if metadata is not None:
        data["metadata_json"] = metadata
    # Ensure sensor_type is used (not type)
    if "type" in data and "sensor_type" not in data:
        data["sensor_type"] = data.pop("type")
    return data


async def list_sensors(session: AsyncSession, machine_id: Optional[UUID] = None) -> List[Sensor]:
    stmt = select(Sensor)
    if machine_id:
        stmt = stmt.where(Sensor.machine_id == machine_id)
    result = await session.execute(stmt.order_by(Sensor.created_at.desc()))
    return result.scalars().all()


async def get_sensor(session: AsyncSession, sensor_id: UUID | str) -> Optional[Sensor]:
    # Handle string IDs (for MQTT auto-registration) - look up by name
    if isinstance(sensor_id, str):
        try:
            # Try to convert to UUID first
            sensor_uuid = UUID(sensor_id)
            result = await session.execute(select(Sensor).where(Sensor.id == sensor_uuid))
            sensor = result.scalars().first()  # Use first() instead of scalar_one_or_none()
            if sensor:
                return sensor
        except ValueError:
            # Not a valid UUID, try finding by name (sensor names are stored as "Sensor {sensor_id}")
            # Also check if name directly matches or contains the sensor_id
            # Use .first() instead of scalar_one_or_none() to handle duplicates
            result = await session.execute(
                select(Sensor).where(
                    (Sensor.name == sensor_id) | 
                    (Sensor.name == f"Sensor {sensor_id}") |
                    (Sensor.name.like(f"%{sensor_id}%"))
                ).order_by(Sensor.created_at.desc())
            )
            sensor = result.scalars().first()  # Get most recent if duplicates exist
            if sensor:
                return sensor
            # Also check metadata for original sensor_id
            from sqlalchemy import func
            result = await session.execute(
                select(Sensor).where(
                    func.json_extract_path_text(Sensor.metadata_json, 'original_sensor_id') == sensor_id
                ).order_by(Sensor.created_at.desc())
            )
            sensor = result.scalars().first()  # Get most recent if duplicates exist
            if sensor:
                return sensor
            return None
    # UUID lookup
    result = await session.execute(select(Sensor).where(Sensor.id == sensor_id))
    return result.scalars().first()


async def create_sensor(session: AsyncSession, payload: SensorCreate) -> Sensor:
    # Create sensor directly from payload to preserve UUIDs (don't use model_dump which converts to strings)
    metadata = payload.metadata
    metadata_json = metadata if metadata is not None else None
    
    sensor = Sensor(
        name=payload.name,
        machine_id=payload.machine_id,  # Keep as UUID object
        sensor_type=payload.sensor_type,
        unit=payload.unit,
        min_threshold=payload.min_threshold,
        max_threshold=payload.max_threshold,
        warning_threshold=payload.warning_threshold,
        critical_threshold=payload.critical_threshold,
        metadata_json=metadata_json,
    )
    session.add(sensor)
    await session.commit()
    await session.refresh(sensor)
    return sensor


async def update_sensor(session: AsyncSession, sensor: Sensor, payload: SensorUpdate) -> Sensor:
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "metadata":
            setattr(sensor, "metadata_json", value)
        else:
            setattr(sensor, field, value)
    await session.commit()
    await session.refresh(sensor)
    return sensor


async def delete_sensor(session: AsyncSession, sensor: Sensor) -> None:
    await session.delete(sensor)
    await session.commit()

