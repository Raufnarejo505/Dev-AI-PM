from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, require_engineer
from app.models.user import User
from app.models.sensor_data import SensorData
from app.models.prediction import Prediction
from app.models.alarm import Alarm

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def get_metrics(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_engineer),
):
    """Get Prometheus-compatible metrics"""
    now = datetime.utcnow()
    last_hour = now - timedelta(hours=1)
    
    # Ingestion rate (sensor data per hour)
    sensor_data_count = await session.scalar(
        select(func.count(SensorData.id)).where(SensorData.created_at >= last_hour)
    )
    ingestion_rate = sensor_data_count or 0
    
    # Prediction latency (average response_time_ms)
    avg_latency = await session.scalar(
        select(func.avg(Prediction.response_time_ms)).where(
            and_(
                Prediction.created_at >= last_hour,
                Prediction.response_time_ms.isnot(None)
            )
        )
    )
    prediction_latency_ms = float(avg_latency) if avg_latency else 0.0
    
    # Active alarms
    active_alarms_count = await session.scalar(
        select(func.count(Alarm.id)).where(Alarm.status == "active")
    )
    
    # Queue depth (MQTT queue size - would need to expose from mqtt_ingestor)
    from app.mqtt.consumer import mqtt_ingestor
    queue_depth = mqtt_ingestor.queue.qsize() if mqtt_ingestor.queue else 0
    
    # Format as Prometheus metrics
    metrics_text = f"""# HELP sensor_data_ingestion_rate Sensor data ingestion rate per hour
# TYPE sensor_data_ingestion_rate gauge
sensor_data_ingestion_rate {ingestion_rate}

# HELP prediction_latency_ms Average prediction latency in milliseconds
# TYPE prediction_latency_ms gauge
prediction_latency_ms {prediction_latency_ms}

# HELP active_alarms_count Number of active alarms
# TYPE active_alarms_count gauge
active_alarms_count {active_alarms_count or 0}

# HELP mqtt_queue_depth MQTT message queue depth
# TYPE mqtt_queue_depth gauge
mqtt_queue_depth {queue_depth}

# HELP system_uptime_seconds System uptime in seconds
# TYPE system_uptime_seconds counter
system_uptime_seconds {int((now - datetime(2025, 1, 1)).total_seconds())}
"""
    
    return metrics_text


@router.get("/json")
async def get_metrics_json(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_engineer),
):
    """Get metrics as JSON (easier for frontend)"""
    now = datetime.utcnow()
    last_hour = now - timedelta(hours=1)
    
    sensor_data_count = await session.scalar(
        select(func.count(SensorData.id)).where(SensorData.created_at >= last_hour)
    )
    
    avg_latency = await session.scalar(
        select(func.avg(Prediction.response_time_ms)).where(
            and_(
                Prediction.created_at >= last_hour,
                Prediction.response_time_ms.isnot(None)
            )
        )
    )
    
    active_alarms_count = await session.scalar(
        select(func.count(Alarm.id)).where(Alarm.status == "active")
    )
    
    from app.mqtt.consumer import mqtt_ingestor
    queue_depth = mqtt_ingestor.queue.qsize() if mqtt_ingestor.queue else 0
    
    return {
        "ingestion_rate_per_hour": sensor_data_count or 0,
        "prediction_latency_ms": float(avg_latency) if avg_latency else 0.0,
        "active_alarms": active_alarms_count or 0,
        "mqtt_queue_depth": queue_depth,
        "timestamp": now.isoformat(),
    }

