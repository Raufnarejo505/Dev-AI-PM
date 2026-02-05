# Complete Fix Guide for Database Migration Issue

## Problem Summary
1. `alembic_version` table doesn't exist (migrations rolled back)
2. When it gets created, it uses VARCHAR(32) which is too small
3. Migration 0004 fails because the name is longer than 32 characters

## Solution: Create Table with Correct Size, Then Run Migrations

### Step 1: Create alembic_version table with VARCHAR(255)

```bash
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(255) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num));"
```

### Step 2: Run the updated fix script

```bash
docker compose -f docker-compose.prod.yml exec backend python scripts/fix_alembic_version.py
```

This will verify the table exists and has the correct size.

### Step 3: Run migrations

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Step 4: Verify tables were created

```bash
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "\dt"
```

Should show: machine, sensor, user, alarm, ticket, etc.

### Step 5: Seed demo data

```bash
docker compose -f docker-compose.prod.yml exec backend python -m app.tasks.seed_demo_data
```

### Step 6: Restart backend

```bash
docker compose -f docker-compose.prod.yml restart backend
```

## Alternative: Clean Start (If Above Doesn't Work)

If you want to start completely fresh:

```bash
# 1. Drop all tables (WARNING: This deletes all data!)
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# 2. Create alembic_version with correct size
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "CREATE TABLE alembic_version (version_num VARCHAR(255) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num));"

# 3. Run migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 4. Seed demo data
docker compose -f docker-compose.prod.yml exec backend python -m app.tasks.seed_demo_data

# 5. Restart backend
docker compose -f docker-compose.prod.yml restart backend
```

## Quick Fix Sequence (Recommended)

```bash
# 1. Create alembic_version table with correct size
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(255) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num));"

# 2. Verify it was created
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "\d alembic_version"

# 3. Run migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 4. Verify all tables
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "\dt"

# 5. Seed demo data
docker compose -f docker-compose.prod.yml exec backend python -m app.tasks.seed_demo_data

# 6. Restart backend
docker compose -f docker-compose.prod.yml restart backend

# 7. Test the application
curl http://localhost:3000/api/health
```

## Expected Results

✅ alembic_version table created with VARCHAR(255)  
✅ All migrations complete successfully  
✅ All tables created (machine, sensor, user, etc.)  
✅ Demo data seeded  
✅ Backend works without errors  
✅ Login works in frontend

