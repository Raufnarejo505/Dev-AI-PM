# Fix Offline Mode and Live Updates

## Problem
Dashboard shows "Offline Mode" and not updating live - frontend can't connect to backend properly.

## Diagnostic Commands (Run on Server)

### Step 1: Check backend is responding

```bash
# Test health endpoint
curl http://localhost:3000/api/health

# Test status endpoint
curl http://localhost:3000/api/status

# Test dashboard endpoint
curl http://localhost:3000/api/dashboard/overview
```

### Step 2: Check backend logs for errors

```bash
docker compose -f docker-compose.prod.yml logs backend --tail=100
```

Look for:
- Connection errors
- Database errors
- API errors
- WebSocket/SSE errors

### Step 3: Test WebSocket/SSE connections

```bash
# Test SSE endpoint
curl -N http://localhost:3000/api/sse/events

# Test WebSocket (if configured)
curl http://localhost:3000/api/ws
```

### Step 4: Check frontend nginx logs

```bash
docker compose -f docker-compose.prod.yml logs frontend --tail=50
```

Look for proxy errors or connection issues.

### Step 5: Verify backend can reach database

```bash
docker compose -f docker-compose.prod.yml exec backend python -c "from app.core.config import get_settings; from app.api.dependencies import get_session; import asyncio; async def test(): session = await get_session().__anext__(); print('DB connected'); asyncio.run(test())"
```

## Common Fixes

### Fix 1: Restart all services

```bash
docker compose -f docker-compose.prod.yml restart
```

### Fix 2: Check CORS configuration

The backend should allow requests from the frontend. Check if CORS is configured correctly.

### Fix 3: Verify nginx proxy configuration

```bash
# Check nginx config inside container
docker compose -f docker-compose.prod.yml exec frontend cat /etc/nginx/conf.d/default.conf
```

### Fix 4: Check if backend has errors

```bash
# View detailed backend logs
docker compose -f docker-compose.prod.yml logs backend --tail=200 | grep -i error
```

### Fix 5: Test API from browser console

Open browser console (F12) and check for:
- Network errors
- CORS errors
- Failed API calls

## Quick Fix Sequence

```bash
# 1. Check backend health
curl http://localhost:3000/api/health

# 2. Check backend status
curl http://localhost:3000/api/status

# 3. Restart backend
docker compose -f docker-compose.prod.yml restart backend

# 4. Wait a few seconds
sleep 5

# 5. Check logs
docker compose -f docker-compose.prod.yml logs backend --tail=50

# 6. Test dashboard endpoint
curl http://localhost:3000/api/dashboard/overview
```

## Expected Results

✅ `curl http://localhost:3000/api/health` returns JSON  
✅ `curl http://localhost:3000/api/status` returns comprehensive status  
✅ `curl http://localhost:3000/api/dashboard/overview` returns dashboard data  
✅ Frontend shows "Backend: Online" instead of "Offline Mode"  
✅ Dashboard updates live without "Offline Mode" banner

