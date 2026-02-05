# Fix Database Tables Missing Error

## Problem
Backend is working, but database tables don't exist:
```
relation "machine" does not exist
```

## Solution: Run Database Migrations

### Step 1: Check if migrations ran

```bash
docker compose -f docker-compose.prod.yml exec backend alembic current
```

### Step 2: Run database migrations

```bash
# Run all pending migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Step 3: Verify tables were created

```bash
# Check if machine table exists
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "\dt"
```

### Step 4: Seed demo data (optional)

```bash
docker compose -f docker-compose.prod.yml exec backend python -m app.tasks.seed_demo_data
```

## If Migrations Fail

### Check database connection

```bash
# Verify database is accessible
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U pm_user

# Test connection from backend
docker compose -f docker-compose.prod.yml exec backend python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('postgresql://pm_user:pm_pass@postgres:5432/pm_db'))"
```

### Restart backend after migrations

```bash
docker compose -f docker-compose.prod.yml restart backend
```

## Quick Fix Sequence

```bash
# 1. Run migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 2. Wait a few seconds
sleep 5

# 3. Seed demo data
docker compose -f docker-compose.prod.yml exec backend python -m app.tasks.seed_demo_data

# 4. Restart backend
docker compose -f docker-compose.prod.yml restart backend

# 5. Test API
curl http://localhost:3000/api/health
```

## Expected Results

✅ Migrations complete without errors  
✅ Tables created (machine, sensor, user, etc.)  
✅ Backend can query database  
✅ Login works without errors

