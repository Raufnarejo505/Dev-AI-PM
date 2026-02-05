# Fix Alembic Version Column Too Small

## Problem
Error: `value too long for type character varying(32)`
The `alembic_version.version_num` column is only 32 characters, but migration names are longer.

## Solution: Run Fix Script First

### Step 1: Run the fix script to expand the column

```bash
docker compose -f docker-compose.prod.yml exec backend python scripts/fix_alembic_version.py
```

This expands the column from VARCHAR(32) to VARCHAR(255).

### Step 2: Run migrations again

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Step 3: Verify tables were created

```bash
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "\dt"
```

You should see tables like: machine, sensor, user, etc.

### Step 4: Seed demo data

```bash
docker compose -f docker-compose.prod.yml exec backend python -m app.tasks.seed_demo_data
```

### Step 5: Restart backend

```bash
docker compose -f docker-compose.prod.yml restart backend
```

## Quick Fix Sequence

```bash
# 1. Fix alembic version column
docker compose -f docker-compose.prod.yml exec backend python scripts/fix_alembic_version.py

# 2. Run migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 3. Verify tables
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "\dt"

# 4. Seed demo data
docker compose -f docker-compose.prod.yml exec backend python -m app.tasks.seed_demo_data

# 5. Restart backend
docker compose -f docker-compose.prod.yml restart backend
```

## Expected Results

✅ Fix script runs without errors  
✅ Migrations complete successfully  
✅ Tables created (machine, sensor, user, etc.)  
✅ Demo data seeded  
✅ Backend works without errors

