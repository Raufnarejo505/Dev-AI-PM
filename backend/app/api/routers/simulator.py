from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_current_user, require_engineer
from app.models.user import User
from app.core.config import get_settings
import paho.mqtt.client as mqtt
import json
import random

router = APIRouter(prefix="/simulator", tags=["simulator"])
settings = get_settings()


class SimulateFailureRequest(BaseModel):
    machine_id: Optional[str] = None
    sensor_id: Optional[str] = None
    anomaly_type: Optional[str] = "critical"  # critical, warning, gradual_drift
    duration: Optional[int] = 60  # seconds
    value_multiplier: Optional[float] = 2.0  # Multiply normal value


@router.post("/generate-test-data")
async def generate_test_data(
    count: int = 10,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Generate test sensor data and predictions directly (alternative to MQTT)
    Useful for testing when MQTT isn't available
    """
    from app.tasks.live_data_generator import generate_live_dummy_data
    
    generated = 0
    for i in range(count):
        await generate_live_dummy_data()
        generated += 1
    
    return {
        "ok": True,
        "message": f"Generated {generated} batches of test data",
        "records_created": generated * 10  # Approximate
    }


@router.post("/trigger-failure")
async def trigger_failure(
    payload: SimulateFailureRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_engineer),
):
    """
    Trigger a simulated failure/anomaly by publishing anomalous sensor data to MQTT.
    This allows testing the full pipeline: MQTT → Backend → AI → Predictions → Alarms
    """
    try:
        # Connect to MQTT broker
        client = mqtt.Client(client_id=f"failure-simulator-{random.randint(1000, 9999)}")
        client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port, keepalive=60)
        client.loop_start()
        
        # Determine which machine/sensor to use
        machine_id = payload.machine_id or "machine-1"
        sensor_id = payload.sensor_id or "pressure-head"
        
        # Generate anomalous values based on anomaly type
        base_value = 140.0  # Normal value
        if payload.anomaly_type == "critical":
            anomalous_value = base_value * payload.value_multiplier  # 2.5x for critical
            status = "critical"
        elif payload.anomaly_type == "warning":
            anomalous_value = base_value * 1.8  # 1.8x for warning
            status = "warning"
        elif payload.anomaly_type == "gradual_drift":
            anomalous_value = base_value * 1.3
            status = "warning"
        else:
            anomalous_value = base_value * payload.value_multiplier
            status = "critical"
        
        # Publish multiple anomalous readings over the duration
        readings_count = min(payload.duration // 2, 30)  # Max 30 readings
        
        for i in range(readings_count):
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Topic format matching simulator - map machine to correct topic
            # Simulator uses: factory/demo/line1/machine1/sensors, factory/demo/line2/machine2/sensors, etc.
            machine_topic_map = {
                "machine-1": "factory/demo/line1/machine1/sensors",
                "machine-2": "factory/demo/line2/machine2/sensors",
                "machine-3": "factory/demo/line3/machine3/sensors",
                "machine-4": "factory/demo/line2/conveyor/sensors",
            }
            
            # Determine topic from machine_id or name
            topic = machine_topic_map.get(machine_id, "factory/demo/line1/machine1/sensors")
            
            # If machine_id is a UUID or name, try to map it
            if machine_id not in machine_topic_map:
                # Try to get machine from database to determine topic
                from app.services import machine_service
                try:
                    machine_obj = await machine_service.get_machine(session, machine_id)
                    if machine_obj and machine_obj.name:
                        machine_name_lower = machine_obj.name.lower()
                        if "pump" in machine_name_lower:
                            topic = "factory/demo/line1/machine1/sensors"
                        elif "motor" in machine_name_lower:
                            topic = "factory/demo/line2/machine2/sensors"
                        elif "compressor" in machine_name_lower:
                            topic = "factory/demo/line3/machine3/sensors"
                        elif "conveyor" in machine_name_lower:
                            topic = "factory/demo/line2/conveyor/sensors"
                except:
                    pass  # Use default topic
            
            mqtt_payload = {
                "sensor_id": sensor_id,
                "machine_id": machine_id,
                "metric": "pressure",
                "value": round(anomalous_value + random.uniform(-5, 5), 2),
                "unit": "psi",
                "status": status,  # Add status field for device state
                "timestamp": timestamp,
                "metadata": {
                    "simulated_failure": True,
                    "anomaly_type": payload.anomaly_type,
                    "device_state": status,
                    "triggered_by": str(current_user.id),
                    "iteration": i + 1,
                }
            }
            
            client.publish(topic, json.dumps(mqtt_payload))
            
            # Small delay between readings
            import asyncio
            await asyncio.sleep(0.5)
        
        client.loop_stop()
        client.disconnect()
        
        return {
            "ok": True,
            "message": f"Simulated {payload.anomaly_type} anomaly for {readings_count} readings",
            "machine_id": machine_id,
            "sensor_id": sensor_id,
            "readings_sent": readings_count,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger simulation: {str(e)}"
        )

