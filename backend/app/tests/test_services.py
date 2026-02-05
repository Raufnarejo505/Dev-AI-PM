from datetime import datetime, timezone
import pytest

from app.schemas.machine import MachineCreate
from app.schemas.prediction import PredictionRequest
from app.schemas.sensor import SensorCreate
from app.schemas.sensor_data import SensorDataIn
from app.services import alarm_service, machine_service, prediction_service, sensor_data_service, sensor_service


@pytest.mark.asyncio
async def test_sensor_ingestion_creates_row(session):
    machine = await machine_service.create_machine(
        session,
        MachineCreate(name="Tester", location="Lab", description="Test rig", status="online", criticality="high"),
    )
    sensor = await sensor_service.create_sensor(
        session,
        SensorCreate(
            machine_id=machine.id,
            name="Pressure",
            sensor_type="pressure",
            unit="psi",
            warning_threshold=150,
            critical_threshold=180,
        ),
    )

    payload = SensorDataIn(
        sensor_id=sensor.id,
        machine_id=machine.id,
        timestamp=datetime.now(timezone.utc),
        value=175,
        status="normal",
    )

    stored = await sensor_data_service.ingest_sensor_data(session, payload)
    assert stored.value == 175
    assert stored.sensor_id == sensor.id


@pytest.mark.asyncio
async def test_alarm_created_on_high_value(session):
    machine = await machine_service.create_machine(
        session, MachineCreate(name="AlarmRig", location="Plant", description="Alarm rig", criticality="high")
    )
    sensor = await sensor_service.create_sensor(
        session,
        SensorCreate(
            machine_id=machine.id,
            name="Temperature",
            sensor_type="temperature",
            unit="C",
            warning_threshold=90,
            critical_threshold=100,
        ),
    )

    alarm = await alarm_service.auto_alarm_from_sensor_value(
        session=session,
        sensor=sensor,
        machine_id=machine.id,
        value=110,
        timestamp=datetime.now(timezone.utc),
    )

    assert alarm is not None
    assert alarm.severity == "critical"


@pytest.mark.asyncio
async def test_prediction_workflow_persists_result(monkeypatch, session):
    machine = await machine_service.create_machine(
        session, MachineCreate(name="Predictor", location="Node", description="Predict test", criticality="medium")
    )
    sensor = await sensor_service.create_sensor(
        session,
        SensorCreate(
            machine_id=machine.id,
            name="Vibration",
            sensor_type="vibration",
            unit="mm/s",
            warning_threshold=4,
            critical_threshold=6,
        ),
    )

    async def fake_call_ai_service(payload):
        return {"prediction": "anomaly", "score": 0.92, "model_version": "stub"}

    monkeypatch.setattr(prediction_service, "call_ai_service", fake_call_ai_service)

    prediction = await prediction_service.run_prediction_workflow(
        session,
        PredictionRequest(
            sensor_id=sensor.id,
            machine_id=machine.id,
            timestamp=datetime.now(timezone.utc),
            value=7.2,
            context={},
        ),
    )

    assert float(prediction.score) == pytest.approx(0.92)
    assert prediction.status == "anomaly"

