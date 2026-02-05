# Fix Backend Connection Issues

## Problem
Frontend shows "Internal Server Error" and "Offline Mode" - can't connect to backend.

## Diagnostic Commands (Run on Server)

### Step 1: Check if all services are running

```bash
docker compose -f docker-compose.prod.yml ps
```

All services should show "Up" status.

### Step 2: Check backend logs

```bash
docker compose -f docker-compose.prod.yml logs backend --tail=50
```

Look for errors or connection issues.

### Step 3: Test backend directly

```bash
# Test backend health endpoint
curl http://localhost:8000/health

# Test from inside the network
docker compose -f docker-compose.prod.yml exec backend curl http://localhost:8000/health
```

### Step 4: Test API through frontend nginx

```bash
# Test if nginx can reach backend
curl http://localhost:3000/api/health

# Check frontend nginx logs
docker compose -f docker-compose.prod.yml logs frontend --tail=50
```

### Step 5: Check if backend container can reach AI service

```bash
docker compose -f docker-compose.prod.yml exec backend curl http://ai-service:8000/health
```

## Common Fixes

### Fix 1: Restart all services

```bash
docker compose -f docker-compose.prod.yml restart
```

### Fix 2: Check backend environment variables

```bash
# Verify .env file exists and has correct values
cat backend/.env | grep -E "POSTGRES|JWT|AI_SERVICE"
```

### Fix 3: Rebuild and restart

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### Fix 4: Check database connection

```bash
# Test database connection
docker compose -f docker-compose.prod.yml exec backend python -c "from app.core.config import get_settings; print(get_settings().postgres_host)"
```

### Fix 5: Verify nginx configuration

The nginx config should proxy `/api/` to `http://backend:8000/`. Check if the volume mount is correct:

```bash
docker compose -f docker-compose.prod.yml exec frontend cat /etc/nginx/conf.d/default.conf
```

## Quick Fix Commands

```bash
# 1. Check service status
docker compose -f docker-compose.prod.yml ps

# 2. View backend logs
docker compose -f docker-compose.prod.yml logs backend --tail=100

# 3. Restart backend
docker compose -f docker-compose.prod.yml restart backend

# 4. Test backend health
curl http://localhost:3000/api/health

# 5. If still failing, restart all
docker compose -f docker-compose.prod.yml restart
```

## Expected Results

After fixes:
- `curl http://localhost:3000/api/health` should return: `{"status":"ok",...}`
- Frontend should connect without "Offline Mode" banner
- Login should work

