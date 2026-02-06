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
    """Create only the extruder machine with specified sensors"""
    import os
    from sqlalchemy import select, delete
    from app.models.sensor import Sensor
    
    async with AsyncSessionLocal() as session:
        # Get the extruder machine name from environment or use default
        extruder_machine_name = os.getenv("MSSQL_MACHINE_NAME", "Extruder-SQL")
        
        # Delete all machines except the extruder machine
        all_machines_result = await session.execute(select(Machine))
        all_machines = all_machines_result.scalars().all()
        
        machines_to_delete = [m for m in all_machines if m.name != extruder_machine_name]
        if machines_to_delete:
            for machine in machines_to_delete:
                # Delete all sensors for this machine first
                await session.execute(
                    delete(Sensor).where(Sensor.machine_id == machine.id)
                )
                await session.delete(machine)
            await session.commit()
            print(f"✓ Deleted {len(machines_to_delete)} non-extruder machine(s)")
        
        # Check if extruder machine exists
        extruder_result = await session.execute(
            select(Machine).where(Machine.name == extruder_machine_name)
        )
        extruder = extruder_result.scalar_one_or_none()
        
        if not extruder:
            # Create the extruder machine
            extruder = await machine_service.create_machine(
                session,
                MachineCreate(
                    name=extruder_machine_name,
                    location="Production Line",
                    status="online",
                    criticality="high",
                    metadata={
                        "type": "extruder",
                        "machine_type": "extruder",
                        "source": "mssql",
                    },
                )
            )
            await session.commit()
            await session.refresh(extruder)
            print(f"✓ Created machine: {extruder.name}")
        else:
            print(f"✓ Machine already exists: {extruder.name}")
        
        # Define the required sensors
        required_sensors = [
            {"name": "ScrewSpeed_rpm", "type": "rpm", "unit": "rpm", "min": 0, "max": 500, "warn": 400, "crit": 450},
            {"name": "Pressure_bar", "type": "pressure", "unit": "bar", "min": 0, "max": 200, "warn": 150, "crit": 180},
            {"name": "Temperaturzonen Zone 1", "type": "temperature", "unit": "°C", "min": 0, "max": 300, "warn": 250, "crit": 280},
            {"name": "Temperaturzonen Zone 2", "type": "temperature", "unit": "°C", "min": 0, "max": 300, "warn": 250, "crit": 280},
            {"name": "Temperaturzonen Zone 3", "type": "temperature", "unit": "°C", "min": 0, "max": 300, "warn": 250, "crit": 280},
            {"name": "Temperaturzonen Zone 4", "type": "temperature", "unit": "°C", "min": 0, "max": 300, "warn": 250, "crit": 280},
        ]
        
        # Get existing sensors for the extruder
        existing_sensors_result = await session.execute(
            select(Sensor).where(Sensor.machine_id == extruder.id)
        )
        existing_sensors = existing_sensors_result.scalars().all()
        existing_sensor_names = {s.name for s in existing_sensors}
        
        # Delete sensors that are not in the required list
        sensors_to_delete = [s for s in existing_sensors if s.name not in {rs["name"] for rs in required_sensors}]
        if sensors_to_delete:
            for sensor in sensors_to_delete:
                await session.delete(sensor)
            await session.commit()
            print(f"  ✓ Deleted {len(sensors_to_delete)} unwanted sensor(s)")
        
        # Create missing sensors
        sensors_created = 0
        for sensor_data in required_sensors:
            if sensor_data["name"] not in existing_sensor_names:
                await sensor_service.create_sensor(
                    session,
                    SensorCreate(
                        name=sensor_data["name"],
                        machine_id=extruder.id,
                        sensor_type=sensor_data["type"],
                        unit=sensor_data["unit"],
                        min_threshold=sensor_data["min"],
                        max_threshold=sensor_data["max"],
                        warning_threshold=sensor_data["warn"],
                        critical_threshold=sensor_data["crit"],
                        metadata={"source": "seed"},
                    )
                )
                sensors_created += 1
        
        if sensors_created > 0:
            await session.commit()
            print(f"  ✓ Created {sensors_created} sensor(s) for {extruder.name}")
        
        total_sensors = len([s for s in existing_sensors if s.name in {rs["name"] for rs in required_sensors}]) + sensors_created
        print(f"  ✓ Total sensors for {extruder.name}: {total_sensors}")


async def main():
    """Run all seed functions"""
    print("Seeding demo data...")
    await seed_demo_users()
    await seed_sample_machines()
    print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())

