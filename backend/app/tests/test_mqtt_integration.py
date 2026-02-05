"""Integration tests for MQTT ingestion flow"""
import pytest
import json
from datetime import datetime, timezone
from uuid import uuid4

from app.db.session import AsyncSessionLocal
from app.models.sensor_data import SensorData
from app.models.prediction import Prediction
from app.models.alarm import Alarm
from sqlalchemy import select


@pytest.mark.asyncio
async def test_mqtt_message_ingestion():
    """Test that MQTT messages are ingested and stored"""
    async with AsyncSessionLocal() as session:
        machine_id = uuid4()
        sensor_id = uuid4()
        
        # Simulate MQTT message
        payload = {
            "machine_id": str(machine_id),
            "sensor_id": str(sensor_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "value": 42.5,
            "status": "normal",
        }
        
        # This would normally be handled by mqtt_ingestor
        # For testing, we can directly call the ingestion service
        from app.services import sensor_data_service
        from app.schemas.sensor_data import SensorDataIn
        
        sensor_data = SensorDataIn(
            sensor_id=sensor_id,
            machine_id=machine_id,
            timestamp=datetime.fromisoformat(payload["timestamp"]),
            value=float(payload["value"]),
            status=payload["status"],
            metadata=payload,
        )
        
        result = await sensor_data_service.ingest_sensor_data(session, sensor_data)
        
        # Verify data was stored
        assert result is not None
        assert result.value == 42.5
        
        # Verify it's in the database
        stored = await session.scalar(
            select(SensorData).where(SensorData.id == result.id)
        )
        assert stored is not None
        assert stored.value == 42.5


@pytest.mark.asyncio
async def test_mqtt_message_with_values_object():
    """Test MQTT message with new values object format"""
    async with AsyncSessionLocal() as session:
        machine_id = uuid4()
        sensor_id = uuid4()
        
        payload = {
            "machine_id": str(machine_id),
            "sensor_id": str(sensor_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "values": {
                "temperature": 45.2,
                "pressure": 101.3,
            },
            "metadata": {"unit": "metric"},
        }
        
        # Extract first numeric value (as MQTT consumer does)
        values = payload.get("values", {})
        numeric_values = {k: v for k, v in values.items() if isinstance(v, (int, float))}
        value = sum(numeric_values.values()) / len(numeric_values)
        
        from app.services import sensor_data_service
        from app.schemas.sensor_data import SensorDataIn
        
        sensor_data = SensorDataIn(
            sensor_id=sensor_id,
            machine_id=machine_id,
            timestamp=datetime.fromisoformat(payload["timestamp"]),
            value=value,
            status="normal",
            metadata=payload,
        )
        
        result = await sensor_data_service.ingest_sensor_data(session, sensor_data)
        assert result is not None
        assert result.value == (45.2 + 101.3) / 2

