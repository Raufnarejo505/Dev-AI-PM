"""Cleanup script to remove all machines except the extruder and unwanted sensors"""
import asyncio
import os
from sqlalchemy import select, delete

from app.db.session import AsyncSessionLocal
from app.models.machine import Machine
from app.models.sensor import Sensor


async def cleanup_machines_and_sensors():
    """Delete all machines except the extruder and all sensors except the required ones"""
    async with AsyncSessionLocal() as session:
        # Get the extruder machine name from environment or use default
        extruder_machine_name = os.getenv("MSSQL_MACHINE_NAME", "Extruder-SQL")
        
        # Required sensor names
        required_sensor_names = {
            "ScrewSpeed_rpm",
            "Pressure_bar",
            "Temperaturzonen Zone 1",
            "Temperaturzonen Zone 2",
            "Temperaturzonen Zone 3",
            "Temperaturzonen Zone 4",
        }
        
        # Get all machines
        all_machines_result = await session.execute(select(Machine))
        all_machines = all_machines_result.scalars().all()
        
        machines_to_delete = [m for m in all_machines if m.name != extruder_machine_name]
        
        if machines_to_delete:
            print(f"Found {len(machines_to_delete)} machine(s) to delete:")
            for machine in machines_to_delete:
                print(f"  - {machine.name} (ID: {machine.id})")
                
                # Delete all sensors for this machine first
                sensors_result = await session.execute(
                    select(Sensor).where(Sensor.machine_id == machine.id)
                )
                sensors = sensors_result.scalars().all()
                
                if sensors:
                    for sensor in sensors:
                        await session.delete(sensor)
                    print(f"    Deleted {len(sensors)} sensor(s) for {machine.name}")
                
                # Delete the machine
                await session.delete(machine)
            
            await session.commit()
            print(f"✓ Deleted {len(machines_to_delete)} machine(s)")
        else:
            print("✓ No non-extruder machines to delete")
        
        # Now clean up sensors on the extruder machine
        extruder_result = await session.execute(
            select(Machine).where(Machine.name == extruder_machine_name)
        )
        extruder = extruder_result.scalar_one_or_none()
        
        if extruder:
            # Get all sensors for the extruder
            sensors_result = await session.execute(
                select(Sensor).where(Sensor.machine_id == extruder.id)
            )
            extruder_sensors = sensors_result.scalars().all()
            
            sensors_to_delete = [s for s in extruder_sensors if s.name not in required_sensor_names]
            
            if sensors_to_delete:
                print(f"\nFound {len(sensors_to_delete)} unwanted sensor(s) on {extruder.name}:")
                for sensor in sensors_to_delete:
                    print(f"  - {sensor.name} (ID: {sensor.id})")
                    await session.delete(sensor)
                
                await session.commit()
                print(f"✓ Deleted {len(sensors_to_delete)} unwanted sensor(s)")
            else:
                print(f"\n✓ All sensors on {extruder.name} are correct")
            
            # Show remaining sensors
            remaining_sensors_result = await session.execute(
                select(Sensor).where(Sensor.machine_id == extruder.id)
            )
            remaining_sensors = remaining_sensors_result.scalars().all()
            if remaining_sensors:
                print(f"\nRemaining sensors on {extruder.name}:")
                for sensor in remaining_sensors:
                    print(f"  - {sensor.name}")
        else:
            print(f"\n⚠ Extruder machine '{extruder_machine_name}' not found. It will be created by the seed script.")
        
        # Final summary
        final_machines_result = await session.execute(select(Machine))
        final_machines = final_machines_result.scalars().all()
        print(f"\n✅ Cleanup complete!")
        print(f"   Total machines: {len(final_machines)}")
        for machine in final_machines:
            sensors_count_result = await session.execute(
                select(Sensor).where(Sensor.machine_id == machine.id)
            )
            sensors_count = len(sensors_count_result.scalars().all())
            print(f"   - {machine.name}: {sensors_count} sensor(s)")


async def main():
    """Run cleanup"""
    print("🧹 Starting cleanup of machines and sensors...")
    await cleanup_machines_and_sensors()
    print("\n✅ Cleanup finished!")


if __name__ == "__main__":
    asyncio.run(main())
