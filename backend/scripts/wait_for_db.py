import asyncio
import os

import asyncpg


async def wait_for_db() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        host = os.getenv("POSTGRES_HOST", "postgres")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "pm_user")
        password = os.getenv("POSTGRES_PASSWORD", "pm_pass")
        db_name = os.getenv("POSTGRES_DB", "pm_db")
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

    retries = int(os.getenv("DB_CONNECT_RETRIES", "90"))
    delay = float(os.getenv("DB_CONNECT_DELAY_SECONDS", "2"))

    for attempt in range(1, retries + 1):
        try:
            async with asyncpg.create_pool(database_url, min_size=1, max_size=1) as pool:
                async with pool.acquire() as conn:
                    await conn.execute("SELECT 1;")
            print("✅ Database connection established.")
            return
        except Exception as exc:  # pragma: no cover - startup only
            print(
                f"[wait_for_db] Attempt {attempt}/{retries} failed: {exc}",
                flush=True,
            )
            await asyncio.sleep(delay)

    raise RuntimeError("Database never became available")


if __name__ == "__main__":
    asyncio.run(wait_for_db())

