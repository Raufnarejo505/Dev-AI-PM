from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alarm import Alarm, AlarmSeverity, AlarmStatus
from app.models.sensor import Sensor
from app.schemas.alarm import AlarmCreate
from app.services import notification_service, ticket_service


def _prepare_payload(data: dict) -> dict:
    metadata = data.pop("metadata", None)
    if metadata is not None:
        data["metadata_json"] = metadata
    return data


def _determine_severity(sensor: Sensor, value: float) -> Optional[str]:
    if sensor.critical_threshold is not None and value >= float(sensor.critical_threshold):
        return AlarmSeverity.critical.value
    if sensor.warning_threshold is not None and value >= float(sensor.warning_threshold):
        return AlarmSeverity.warning.value
    if sensor.min_threshold is not None and value <= float(sensor.min_threshold):
        return AlarmSeverity.warning.value
    return None


async def create_alarm(
    session: AsyncSession,
    payload: AlarmCreate,
) -> Alarm:
    data = _prepare_payload(payload.model_dump())
    alarm = Alarm(**data, status=AlarmStatus.open.value)
    session.add(alarm)
    await session.commit()
    await session.refresh(alarm)
    
    # Broadcast real-time update
    try:
        from app.api.routers.realtime import broadcast_update
        await broadcast_update(
            "alarm.created",
            {
                "id": str(alarm.id),
                "machine_id": str(alarm.machine_id),
                "sensor_id": str(alarm.sensor_id) if alarm.sensor_id else None,
                "severity": alarm.severity,
                "message": alarm.message,
                "status": alarm.status,
                "triggered_at": alarm.triggered_at.isoformat() if alarm.triggered_at else None,
            }
        )
    except Exception as e:
        logger.debug(f"Failed to broadcast alarm update: {e}")
    
    return alarm


async def get_active_alarm_by_incident_key(
    session: AsyncSession,
    *,
    machine_id: UUID,
    incident_key: str,
) -> Optional[Alarm]:
    result = await session.execute(
        select(Alarm).where(
            Alarm.machine_id == machine_id,
            Alarm.status.in_([AlarmStatus.open.value, AlarmStatus.acknowledged.value]),
        )
    )
    alarms = list(result.scalars().all())
    for alarm in alarms:
        if (alarm.metadata_json or {}).get("incident_key") == incident_key:
            return alarm
    return None


async def get_alarm_by_incident_key(
    session: AsyncSession,
    *,
    machine_id: UUID,
    incident_key: str,
) -> Optional[Alarm]:
    result = await session.execute(select(Alarm).where(Alarm.machine_id == machine_id))
    alarms = list(result.scalars().all())
    for alarm in alarms:
        if (alarm.metadata_json or {}).get("incident_key") == incident_key:
            return alarm
    return None


async def list_active_incident_alarms(
    session: AsyncSession,
    *,
    machine_id: UUID,
) -> list[Alarm]:
    result = await session.execute(
        select(Alarm).where(
            Alarm.machine_id == machine_id,
            Alarm.status.in_([AlarmStatus.open.value, AlarmStatus.acknowledged.value]),
        )
    )
    alarms = list(result.scalars().all())
    return [a for a in alarms if (a.metadata_json or {}).get("incident_key")]


async def resolve_alarm(session: AsyncSession, alarm: Alarm, resolution_notes: Optional[str] = None) -> Alarm:
    alarm.status = AlarmStatus.resolved.value
    alarm.resolved_at = datetime.now(timezone.utc)
    if resolution_notes:
        if alarm.metadata_json is None:
            alarm.metadata_json = {}
        alarm.metadata_json["resolution_notes"] = resolution_notes
    await session.commit()
    await session.refresh(alarm)
    
    # Broadcast real-time update
    try:
        from app.api.routers.realtime import broadcast_update
        await broadcast_update(
            "alarm.updated",
            {
                "id": str(alarm.id),
                "machine_id": str(alarm.machine_id),
                "status": alarm.status,
                "resolved_at": alarm.resolved_at.isoformat() if alarm.resolved_at else None,
            }
        )
    except Exception as e:
        logger.debug(f"Failed to broadcast alarm update: {e}")
    
    return alarm


async def auto_alarm_from_sensor_value(
    session: AsyncSession,
    sensor: Sensor,
    machine_id: UUID,
    value: float,
    timestamp: datetime,
) -> Optional[Alarm]:
    severity = _determine_severity(sensor, value)
    if not severity:
        return None

    payload = AlarmCreate(
        machine_id=machine_id,
        sensor_id=sensor.id,
        prediction_id=None,
        severity=severity,
        message=f"{sensor.name} reported {value} {sensor.unit or ''}",
        triggered_at=timestamp,
        metadata={"value": value},
    )
    alarm = await create_alarm(session, payload)
    notification_service.enqueue_alarm_notification(alarm, sensor)
    await ticket_service.ensure_ticket_for_alarm(session, alarm)
    logger.warning("Alarm created for sensor {} value {}", sensor.id, value)
    # Note: broadcast_update is already called in create_alarm
    return alarm

