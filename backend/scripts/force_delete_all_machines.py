#!/usr/bin/env python3
"""
Force delete ALL machines from database
This script directly deletes from the database, bypassing any constraints
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


async def force_delete_all_machines():
    """Force delete all machines using raw SQL"""
    
    async with AsyncSessionLocal() as session:
        try:
            # First, check current count
            result = await session.execute(text("SELECT COUNT(*) FROM machine"))
            count_before = result.scalar()
            logger.info(f"Found {count_before} machines before deletion")
            
            if count_before == 0:
                logger.info("No machines to delete")
                return
            
            # Delete all machines using raw SQL (bypasses ORM)
            # This will cascade delete related data due to foreign key constraints
            await session.execute(text("DELETE FROM machine"))
            await session.commit()
            
            # Verify deletion
            result = await session.execute(text("SELECT COUNT(*) FROM machine"))
            count_after = result.scalar()
            
            logger.info(f"✅ Deleted {count_before} machines")
            logger.info(f"✅ Remaining machines: {count_after}")
            
            if count_after > 0:
                logger.warning(f"⚠️  Warning: {count_after} machines still exist!")
            else:
                logger.info("✅ All machines deleted successfully!")
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await session.rollback()
            raise


if __name__ == "__main__":
    logger.info("🚀 Starting force delete all machines script...")
    asyncio.run(force_delete_all_machines())
    logger.info("✅ Script completed")
