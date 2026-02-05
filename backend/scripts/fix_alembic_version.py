"""Script to fix alembic_version table column size"""
import asyncio
import os
import asyncpg


async def fix_alembic_version():
    """Expand alembic_version.version_num column to support longer revision names"""
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    user = os.getenv("POSTGRES_USER", "pm_user")
    password = os.getenv("POSTGRES_PASSWORD", "pm_pass")
    db_name = os.getenv("POSTGRES_DB", "pm_db")
    
    conn = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db_name
    )
    
    try:
        # Check if table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'alembic_version'
            );
        """)
        
        if table_exists:
            # Get current column type
            current_type = await conn.fetchval("""
                SELECT data_type || COALESCE('(' || character_maximum_length || ')', '')
                FROM information_schema.columns 
                WHERE table_name = 'alembic_version' 
                AND column_name = 'version_num';
            """)
            
            print(f"Current version_num type: {current_type}")
            
            # Alter column to support longer names
            await conn.execute("""
                ALTER TABLE alembic_version 
                ALTER COLUMN version_num TYPE VARCHAR(255);
            """)
            
            print("✅ Successfully expanded alembic_version.version_num to VARCHAR(255)")
        else:
            # Create the table with VARCHAR(255) from the start
            print("⚠️  alembic_version table does not exist - creating it with VARCHAR(255)")
            await conn.execute("""
                CREATE TABLE alembic_version (
                    version_num VARCHAR(255) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                );
            """)
            print("✅ Successfully created alembic_version table with VARCHAR(255)")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(fix_alembic_version())

