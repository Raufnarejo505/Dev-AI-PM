import asyncio
from datetime import datetime, timezone

from app.db.session import AsyncSessionLocal
from app.schemas.machine import MachineCreate
from app.schemas.sensor import SensorCreate
from app.services import machine_service, sensor_service

SEED_MACHINES = [
    MachineCreate(name="Compressor A", location="Plant 1", description="Primary compressor", criticality="high"),
    MachineCreate(name="Pump B", location="Plant 1", description="Feed pump", criticality="medium"),
]

SEED_SENSORS = [
    {"machine": "Compressor A", "data": SensorCreate(machine_id=None, name="Pressure", sensor_type="pressure", unit="psi", warning_threshold=160, critical_threshold=180)},  # type: ignore
    {"machine": "Compressor A", "data": SensorCreate(machine_id=None, name="Temperature", sensor_type="temperature", unit="C", warning_threshold=250, critical_threshold=280)},  # type: ignore
    {"machine": "Pump B", "data": SensorCreate(machine_id=None, name="Vibration", sensor_type="vibration", unit="mm/s", warning_threshold=4, critical_threshold=6)},  # type: ignore
]


async def run():
    async with AsyncSessionLocal() as session:
        machines = {}
        for machine in SEED_MACHINES:
            created = await machine_service.create_machine(session, machine)
            machines[created.name] = created

        for sensor in SEED_SENSORS:
            schema = sensor["data"]
            schema.machine_id = machines[sensor["machine"]].id
            await sensor_service.create_sensor(session, schema)


if __name__ == "__main__":
    asyncio.run(run())

