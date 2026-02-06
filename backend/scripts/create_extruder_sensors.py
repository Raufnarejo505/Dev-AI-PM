"""Simple script to create extruder sensors without triggering SQLAlchemy relationship issues"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, '/app')

from app.db.session import AsyncSessionLocal
from app.schemas.sensor import SensorCreate
from app.services import sensor_service


async def create_sensors():
    """Create the required sensors for the extruder machine"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, text
        from app.models.machine import Machine
        
        # Get the extruder machine
        extruder_name = os.getenv("MSSQL_MACHINE_NAME", "Extruder-SQL")
        result = await session.execute(
            select(Machine).where(Machine.name == extruder_name)
        )
        extruder = result.scalar_one_or_none()
        
        if not extruder:
            print(f"❌ Extruder machine '{extruder_name}' not found!")
            return
        
        print(f"✓ Found extruder machine: {extruder.name} (ID: {extruder.id})")
        
        # Define required sensors
        required_sensors = [
            {"name": "ScrewSpeed_rpm", "type": "rpm", "unit": "rpm", "min": 0, "max": 500, "warn": 400, "crit": 450},
            {"name": "Pressure_bar", "type": "pressure", "unit": "bar", "min": 0, "max": 200, "warn": 150, "crit": 180},
            {"name": "Temperaturzonen Zone 1", "type": "temperature", "unit": "°C", "min": 0, "max": 300, "warn": 250, "crit": 280},
            {"name": "Temperaturzonen Zone 2", "type": "temperature", "unit": "°C", "min": 0, "max": 300, "warn": 250, "crit": 280},
            {"name": "Temperaturzonen Zone 3", "type": "temperature", "unit": "°C", "min": 0, "max": 300, "warn": 250, "crit": 280},
            {"name": "Temperaturzonen Zone 4", "type": "temperature", "unit": "°C", "min": 0, "max": 300, "warn": 250, "crit": 280},
        ]
        
        created_count = 0
        for sensor_data in required_sensors:
            try:
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
                created_count += 1
                print(f"  ✓ Created sensor: {sensor_data['name']}")
            except Exception as e:
                print(f"  ⚠ Error creating sensor {sensor_data['name']}: {e}")
        
        await session.commit()
        print(f"\n✅ Created {created_count} sensor(s) for {extruder.name}")


if __name__ == "__main__":
    asyncio.run(create_sensors())
