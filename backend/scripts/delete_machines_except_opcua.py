#!/usr/bin/env python3
"""
Script to delete all machines except "OPCUA-Simulation-Machine"

This script will:
1. Find all machines in the database
2. Keep only "OPCUA-Simulation-Machine"
3. Delete all other machines (cascade deletes related sensors, data, predictions, alarms, tickets)

Usage:
    docker-compose exec backend python /app/scripts/delete_machines_except_opcua.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from sqlalchemy import select
from loguru import logger

from app.db.session import AsyncSessionLocal
from app.models.machine import Machine
from app.services import machine_service


async def delete_machines_except_opcua():
    """Delete all machines except OPCUA-Simulation-Machine"""
    
    async with AsyncSessionLocal() as session:
        try:
            # Get all machines
            result = await session.execute(select(Machine).order_by(Machine.created_at))
            all_machines = result.scalars().all()
            
            if not all_machines:
                logger.info("No machines found in database")
                return
            
            logger.info(f"Found {len(all_machines)} machine(s) in database")
            
            # Find OPCUA-Simulation-Machine
            opcua_machine = None
            machines_to_delete = []
            
            for machine in all_machines:
                if machine.name == "OPCUA-Simulation-Machine":
                    opcua_machine = machine
                    logger.info(f"✅ Found machine to keep: {machine.name} (ID: {machine.id})")
                else:
                    machines_to_delete.append(machine)
                    logger.info(f"  - Will delete: {machine.name} (ID: {machine.id})")
            
            if not opcua_machine:
                logger.warning("⚠️  OPCUA-Simulation-Machine not found! All machines will be deleted.")
                response = input("Continue? (yes/no): ")
                if response.lower() != "yes":
                    logger.info("Cancelled by user")
                    return
            
            if not machines_to_delete:
                logger.info("✅ No machines to delete. Only OPCUA-Simulation-Machine exists.")
                return
            
            # Confirm deletion
            logger.warning(f"\n⚠️  WARNING: About to delete {len(machines_to_delete)} machine(s)")
            logger.warning("This will also delete:")
            logger.warning("  - All sensors associated with these machines")
            logger.warning("  - All sensor data")
            logger.warning("  - All predictions")
            logger.warning("  - All alarms")
            logger.warning("  - All tickets")
            
            response = input("\nProceed with deletion? (yes/no): ")
            if response.lower() != "yes":
                logger.info("Cancelled by user")
                return
            
            # Delete machines
            deleted_count = 0
            for machine in machines_to_delete:
                try:
                    logger.info(f"Deleting machine: {machine.name} (ID: {machine.id})")
                    await machine_service.delete_machine(session, machine)
                    deleted_count += 1
                    logger.info(f"✅ Deleted: {machine.name}")
                except Exception as e:
                    logger.error(f"❌ Failed to delete {machine.name}: {e}")
                    await session.rollback()
            
            logger.info(f"\n✅ Successfully deleted {deleted_count} machine(s)")
            logger.info(f"✅ Kept machine: OPCUA-Simulation-Machine")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await session.rollback()
            raise


if __name__ == "__main__":
    logger.info("🚀 Starting machine cleanup script...")
    logger.info("   Keeping: OPCUA-Simulation-Machine")
    logger.info("   Deleting: All other machines\n")
    
    asyncio.run(delete_machines_except_opcua())
    
    logger.info("\n✅ Script completed")
