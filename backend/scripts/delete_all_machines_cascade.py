#!/usr/bin/env python3
"""
Delete ALL machines and all related data (cascade delete)
This handles foreign key constraints by deleting in the correct order
"""

import asyncio
import sys
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from sqlalchemy import text
from loguru import logger

from app.db.session import AsyncSessionLocal


async def delete_all_machines_cascade():
    """Delete all machines and related data in correct order"""
    
    async with AsyncSessionLocal() as session:
        try:
            # Check counts before deletion
            result = await session.execute(text("SELECT COUNT(*) FROM machine"))
            machines_before = result.scalar()
            result = await session.execute(text("SELECT COUNT(*) FROM prediction"))
            predictions_before = result.scalar()
            result = await session.execute(text("SELECT COUNT(*) FROM sensor_data"))
            sensor_data_before = result.scalar()
            result = await session.execute(text("SELECT COUNT(*) FROM sensor"))
            sensors_before = result.scalar()
            
            logger.info(f"Before deletion:")
            logger.info(f"  Machines: {machines_before}")
            logger.info(f"  Predictions: {predictions_before}")
            logger.info(f"  Sensor Data: {sensor_data_before}")
            logger.info(f"  Sensors: {sensors_before}")
            
            if machines_before == 0:
                logger.info("No machines to delete")
                return
            
            # Delete in correct order to handle foreign key constraints
            logger.info("Deleting related data...")
            
            # 1. Delete predictions (references machine)
            await session.execute(text("DELETE FROM prediction"))
            logger.info("  ✓ Deleted predictions")
            
            # 2. Delete alarms (references machine)
            await session.execute(text("DELETE FROM alarm"))
            logger.info("  ✓ Deleted alarms")
            
            # 3. Delete tickets (references machine)
            await session.execute(text("DELETE FROM ticket"))
            logger.info("  ✓ Deleted tickets")
            
            # 4. Delete sensor_data (references machine)
            await session.execute(text("DELETE FROM sensor_data"))
            logger.info("  ✓ Deleted sensor_data")
            
            # 5. Delete sensors (references machine)
            await session.execute(text("DELETE FROM sensor"))
            logger.info("  ✓ Deleted sensors")
            
            # 6. Now delete machines
            await session.execute(text("DELETE FROM machine"))
            logger.info("  ✓ Deleted machines")
            
            # Commit all deletions
            await session.commit()
            
            # Verify deletion
            result = await session.execute(text("SELECT COUNT(*) FROM machine"))
            machines_after = result.scalar()
            result = await session.execute(text("SELECT COUNT(*) FROM prediction"))
            predictions_after = result.scalar()
            result = await session.execute(text("SELECT COUNT(*) FROM sensor_data"))
            sensor_data_after = result.scalar()
            result = await session.execute(text("SELECT COUNT(*) FROM sensor"))
            sensors_after = result.scalar()
            
            logger.info(f"\nAfter deletion:")
            logger.info(f"  Machines: {machines_after}")
            logger.info(f"  Predictions: {predictions_after}")
            logger.info(f"  Sensor Data: {sensor_data_after}")
            logger.info(f"  Sensors: {sensors_after}")
            
            if machines_after == 0:
                logger.info("\n✅ All machines and related data deleted successfully!")
            else:
                logger.warning(f"\n⚠️  Warning: {machines_after} machines still exist!")
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await session.rollback()
            raise


if __name__ == "__main__":
    logger.info("🚀 Starting cascade delete all machines script...")
    logger.info("   This will delete ALL machines and ALL related data!")
    logger.info("")
    asyncio.run(delete_all_machines_cascade())
    logger.info("\n✅ Script completed")
