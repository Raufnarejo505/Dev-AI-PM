# Manual Fix for Alembic Version Column

## Problem
The `alembic_version` table was created with VARCHAR(32), but migration 0004 has a name longer than 32 characters.

## Solution: Manually Expand the Column

### Step 1: Connect to database and fix the column

```bash
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255);"
```

### Step 2: Verify the column was expanded

```bash
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "\d alembic_version"
```

Should show `version_num | character varying(255)`

### Step 3: Continue migrations

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Step 4: Verify all tables were created

```bash
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "\dt"
```

### Step 5: Seed demo data

```bash
docker compose -f docker-compose.prod.yml exec backend python -m app.tasks.seed_demo_data
```

### Step 6: Restart backend

```bash
docker compose -f docker-compose.prod.yml restart backend
```

## Quick Fix Sequence

```bash
# 1. Fix the column size
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255);"

# 2. Verify it worked
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "\d alembic_version"

# 3. Continue migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 4. Verify tables
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "\dt"

# 5. Seed demo data
docker compose -f docker-compose.prod.yml exec backend python -m app.tasks.seed_demo_data

# 6. Restart backend
docker compose -f docker-compose.prod.yml restart backend
```

## Expected Results

✅ Column expanded to VARCHAR(255)  
✅ Migrations complete successfully  
✅ All tables created  
✅ Demo data seeded  
✅ Backend works without errors

