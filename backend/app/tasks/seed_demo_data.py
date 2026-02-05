"""Seed script for demo users and sample data"""
import asyncio
from uuid import uuid4

from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.machine import Machine
from app.models.sensor import Sensor
from app.schemas.machine import MachineCreate
from app.schemas.sensor import SensorCreate
from app.services import machine_service, sensor_service


async def seed_demo_users():
    """Create demo user accounts"""
    async with AsyncSessionLocal() as session:
        # Check if users already exist
        from app.services import user_service
        
        admin = await user_service.get_user_by_email(session, "admin@example.com")
        if not admin:
            admin = User(
                email="admin@example.com",
                full_name="Admin User",
                role="admin",
                hashed_password=get_password_hash("admin123"),
            )
            session.add(admin)
            print("✓ Created admin user: admin@example.com / admin123")
        
        engineer = await user_service.get_user_by_email(session, "engineer@example.com")
        if not engineer:
            engineer = User(
                email="engineer@example.com",
                full_name="Engineer User",
                role="engineer",
                hashed_password=get_password_hash("engineer123"),
            )
            session.add(engineer)
            print("✓ Created engineer user: engineer@example.com / engineer123")
        
        viewer = await user_service.get_user_by_email(session, "viewer@example.com")
        if not viewer:
            viewer = User(
                email="viewer@example.com",
                full_name="Viewer User",
                role="viewer",
                hashed_password=get_password_hash("viewer123"),
            )
            session.add(viewer)
            print("✓ Created viewer user: viewer@example.com / viewer123")
        
        await session.commit()


async def seed_sample_machines():
    """Create sample machines and sensors matching simulator configuration"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        
        # Machine 1: Pump-01
        pump_result = await session.execute(
            select(Machine).where(Machine.name == "Pump-01")
        )
        pump = pump_result.scalar_one_or_none()
        
        if not pump:
            pump_id = uuid4()
            pump = await machine_service.create_machine(
                session,
                MachineCreate(
                    id=pump_id,
                    name="Pump-01",
                    location="Building A, Floor 2",
                    status="online",
                    criticality="high",
                    metadata={"type": "centrifugal_pump", "machine_id": "machine-1"},
                )
            )
            await session.commit()
            await session.refresh(pump)
            print(f"✓ Created machine: {pump.name}")
            
            # Create sensors matching simulator
            sensors_pump = [
                {"name": "Pressure Sensor", "sensor_id": "pressure-head", "type": "pressure", "unit": "psi", "min": 100, "max": 180, "warn": 150, "crit": 180},
                {"name": "Temperature Sensor", "sensor_id": "temp-core", "type": "temperature", "unit": "°C", "min": 200, "max": 260, "warn": 250, "crit": 280},
                {"name": "Vibration Sensor", "sensor_id": "vibe-x", "type": "vibration", "unit": "mm/s", "min": 2, "max": 5, "warn": 4, "crit": 6},
                {"name": "Flow Sensor", "sensor_id": "flow-rate", "type": "flow", "unit": "L/min", "min": 50, "max": 150, "warn": 130, "crit": 145},
            ]
            for sensor_data in sensors_pump:
                await sensor_service.create_sensor(
                    session,
                    SensorCreate(
                        id=uuid4(),
                        name=sensor_data["name"],
                        machine_id=pump.id,
                        sensor_type=sensor_data["type"],
                        unit=sensor_data["unit"],
                        min_threshold=sensor_data["min"],
                        max_threshold=sensor_data["max"],
                        warning_threshold=sensor_data["warn"],
                        critical_threshold=sensor_data["crit"],
                        metadata={"sensor_id": sensor_data["sensor_id"]},
                    )
                )
            await session.commit()
            print(f"  ✓ Created {len(sensors_pump)} sensors for {pump.name}")
        
        # Machine 2: Motor-02
        motor_result = await session.execute(
            select(Machine).where(Machine.name == "Motor-02")
        )
        motor = motor_result.scalar_one_or_none()
        
        if not motor:
            motor_id = uuid4()
            motor = await machine_service.create_machine(
                session,
                MachineCreate(
                    id=motor_id,
                    name="Motor-02",
                    location="Building B, Floor 1",
                    status="online",
                    criticality="medium",
                    metadata={"type": "electric_motor", "machine_id": "machine-2"},
                )
            )
            await session.commit()
            await session.refresh(motor)
            print(f"✓ Created machine: {motor.name}")
            
            sensors_motor = [
                {"name": "Current Sensor", "sensor_id": "current-phase-a", "type": "current", "unit": "A", "min": 10, "max": 50, "warn": 18, "crit": 22},
                {"name": "Temperature Sensor", "sensor_id": "temp-winding", "type": "temperature", "unit": "°C", "min": 60, "max": 120, "warn": 100, "crit": 110},
                {"name": "Vibration Sensor", "sensor_id": "vibration-base", "type": "vibration", "unit": "mm/s", "min": 1, "max": 4, "warn": 3.5, "crit": 4.5},
                {"name": "RPM Sensor", "sensor_id": "rpm-shaft", "type": "rpm", "unit": "rpm", "min": 1400, "max": 1600, "warn": 1550, "crit": 1580},
            ]
            for sensor_data in sensors_motor:
                await sensor_service.create_sensor(
                    session,
                    SensorCreate(
                        id=uuid4(),
                        name=sensor_data["name"],
                        machine_id=motor.id,
                        sensor_type=sensor_data["type"],
                        unit=sensor_data["unit"],
                        min_threshold=sensor_data["min"],
                        max_threshold=sensor_data["max"],
                        warning_threshold=sensor_data["warn"],
                        critical_threshold=sensor_data["crit"],
                        metadata={"sensor_id": sensor_data["sensor_id"]},
                    )
                )
            await session.commit()
            print(f"  ✓ Created {len(sensors_motor)} sensors for {motor.name}")
        
        # Machine 3: Compressor-A
        compressor_result = await session.execute(
            select(Machine).where(Machine.name == "Compressor-A")
        )
        compressor = compressor_result.scalar_one_or_none()
        
        if not compressor:
            compressor_id = uuid4()
            compressor = await machine_service.create_machine(
                session,
                MachineCreate(
                    id=compressor_id,
                    name="Compressor-A",
                    location="Building C, Floor 3",
                    status="online",
                    criticality="high",
                    metadata={"type": "air_compressor", "machine_id": "machine-3"},
                )
            )
            await session.commit()
            await session.refresh(compressor)
            print(f"✓ Created machine: {compressor.name}")
            
            sensors_compressor = [
                {"name": "Pressure Sensor", "sensor_id": "pressure-tank", "type": "pressure", "unit": "bar", "min": 6, "max": 10, "warn": 9, "crit": 9.5},
                {"name": "Temperature Sensor", "sensor_id": "temp-discharge", "type": "temperature", "unit": "°C", "min": 40, "max": 90, "warn": 75, "crit": 85},
                {"name": "Oil Level Sensor", "sensor_id": "oil-level", "type": "oil_level", "unit": "%", "min": 40, "max": 100, "warn": 50, "crit": 45},
                {"name": "Vibration Sensor", "sensor_id": "vibration-1", "type": "vibration", "unit": "mm/s", "min": 1.5, "max": 4.5, "warn": 3.5, "crit": 4.5},
            ]
            for sensor_data in sensors_compressor:
                await sensor_service.create_sensor(
                    session,
                    SensorCreate(
                        id=uuid4(),
                        name=sensor_data["name"],
                        machine_id=compressor.id,
                        sensor_type=sensor_data["type"],
                        unit=sensor_data["unit"],
                        min_threshold=sensor_data["min"],
                        max_threshold=sensor_data["max"],
                        warning_threshold=sensor_data["warn"],
                        critical_threshold=sensor_data["crit"],
                        metadata={"sensor_id": sensor_data["sensor_id"]},
                    )
                )
            await session.commit()
            print(f"  ✓ Created {len(sensors_compressor)} sensors for {compressor.name}")
        
        # Machine 4: Conveyor-B2
        conveyor_result = await session.execute(
            select(Machine).where(Machine.name == "Conveyor-B2")
        )
        conveyor = conveyor_result.scalar_one_or_none()
        
        if not conveyor:
            conveyor_id = uuid4()
            conveyor = await machine_service.create_machine(
                session,
                MachineCreate(
                    id=conveyor_id,
                    name="Conveyor-B2",
                    location="Building B, Floor 2",
                    status="online",
                    criticality="medium",
                    metadata={"type": "conveyor_belt", "machine_id": "machine-4"},
                )
            )
            await session.commit()
            await session.refresh(conveyor)
            print(f"✓ Created machine: {conveyor.name}")
            
            sensors_conveyor = [
                {"name": "Speed Sensor", "sensor_id": "speed-belt", "type": "speed", "unit": "m/s", "min": 0.5, "max": 2.5, "warn": 2.2, "crit": 2.4},
                {"name": "Load Sensor", "sensor_id": "load-weight", "type": "load", "unit": "kg", "min": 0, "max": 500, "warn": 450, "crit": 480},
                {"name": "Temperature Sensor", "sensor_id": "temp-bearing", "type": "temperature", "unit": "°C", "min": 25, "max": 70, "warn": 60, "crit": 65},
                {"name": "Torque Sensor", "sensor_id": "torque-motor", "type": "torque", "unit": "Nm", "min": 50, "max": 200, "warn": 180, "crit": 190},
            ]
            for sensor_data in sensors_conveyor:
                await sensor_service.create_sensor(
                    session,
                    SensorCreate(
                        id=uuid4(),
                        name=sensor_data["name"],
                        machine_id=conveyor.id,
                        sensor_type=sensor_data["type"],
                        unit=sensor_data["unit"],
                        min_threshold=sensor_data["min"],
                        max_threshold=sensor_data["max"],
                        warning_threshold=sensor_data["warn"],
                        critical_threshold=sensor_data["crit"],
                        metadata={"sensor_id": sensor_data["sensor_id"]},
                    )
                )
            await session.commit()
            print(f"  ✓ Created {len(sensors_conveyor)} sensors for {conveyor.name}")


async def main():
    """Run all seed functions"""
    print("Seeding demo data...")
    await seed_demo_users()
    await seed_sample_machines()
    print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())

