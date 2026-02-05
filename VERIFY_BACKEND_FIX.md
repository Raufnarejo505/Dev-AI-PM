# Verify Backend Connection After Restart

## ✅ Backend Restarted Successfully

The backend container restarted (return code 0 = success). Now verify it's working.

## Verification Commands (Run on Server)

### Step 1: Check backend is running

```bash
docker compose -f docker-compose.prod.yml ps backend
```

Should show: `Up` status

### Step 2: Check backend logs (look for startup errors)

```bash
docker compose -f docker-compose.prod.yml logs backend --tail=50
```

Look for:
- ✅ "Application startup complete"
- ✅ "Uvicorn running on"
- ❌ Any error messages

### Step 3: Test backend health endpoint

```bash
# Test through nginx proxy (how frontend accesses it)
curl http://localhost:3000/api/health

# Test backend directly
curl http://localhost:8000/health
```

Expected response: `{"status":"ok",...}`

### Step 4: Test login endpoint

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

### Step 5: Check if frontend can reach backend

```bash
# Test from inside frontend container
docker compose -f docker-compose.prod.yml exec frontend wget -qO- http://backend:8000/health
```

## If Backend Still Not Working

### Check database connection

```bash
# Verify database is accessible
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U pm_user

# Test backend can connect to database
docker compose -f docker-compose.prod.yml exec backend python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('postgresql://pm_user:pm_pass@postgres:5432/pm_db'))"
```

### Check environment variables

```bash
# Verify backend has correct environment
docker compose -f docker-compose.prod.yml exec backend env | grep -E "POSTGRES|JWT|AI_SERVICE"
```

### Restart all services if needed

```bash
docker compose -f docker-compose.prod.yml restart
```

## Quick Test Sequence

```bash
# 1. Check status
docker compose -f docker-compose.prod.yml ps

# 2. Test API
curl http://localhost:3000/api/health

# 3. If fails, check logs
docker compose -f docker-compose.prod.yml logs backend --tail=100

# 4. If still fails, restart all
docker compose -f docker-compose.prod.yml restart
```

## Expected Results

✅ `curl http://localhost:3000/api/health` returns JSON with `"status":"ok"`  
✅ Frontend can connect (no "Offline Mode" banner)  
✅ Login works without "Internal Server Error"

---

**Note**: The WinSCP error dialog is misleading - return code 0 means success! The backend restarted correctly.

