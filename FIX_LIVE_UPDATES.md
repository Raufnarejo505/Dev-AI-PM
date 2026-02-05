# Fix Offline Mode and Enable Live Updates

## Problem
Dashboard shows "Offline Mode" and not updating live - frontend can't properly connect to backend.

## Root Cause
The frontend health check is likely failing, causing it to think the backend is offline.

## Diagnostic Commands (Run on Server)

### Step 1: Test health endpoints

```bash
# Test basic health (no auth required)
curl http://localhost:3000/api/health

# Test live health (no auth required)
curl http://localhost:3000/api/health/live

# Test status endpoint
curl http://localhost:3000/api/status
```

### Step 2: Test dashboard endpoint (requires auth)

```bash
# This will fail without token - that's expected
curl http://localhost:3000/api/dashboard/overview
```

### Step 3: Check backend logs

```bash
docker compose -f docker-compose.prod.yml logs backend --tail=100 | grep -i error
```

### Step 4: Check frontend nginx logs

```bash
docker compose -f docker-compose.prod.yml logs frontend --tail=50
```

### Step 5: Test from browser console

Open browser console (F12) and run:
```javascript
// Test health endpoint
fetch('/api/health/live')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

## Quick Fixes

### Fix 1: Restart all services

```bash
docker compose -f docker-compose.prod.yml restart
```

### Fix 2: Check if health/live is accessible

```bash
# Should return JSON
curl http://localhost:3000/api/health/live
```

### Fix 3: Verify nginx is proxying correctly

```bash
# Check nginx config
docker compose -f docker-compose.prod.yml exec frontend cat /etc/nginx/conf.d/default.conf | grep -A 5 "/api"
```

### Fix 4: Clear browser cache and reload

In browser:
- Press Ctrl+Shift+R (hard refresh)
- Or clear cache and reload

## Expected Results

✅ `curl http://localhost:3000/api/health/live` returns: `{"status":"alive",...}`  
✅ Browser console shows successful health check  
✅ Frontend shows "Backend: Online"  
✅ Dashboard updates live without "Offline Mode" banner  
✅ Auto-refresh works

## If Still Not Working

Check browser console (F12) for:
- Network errors
- CORS errors
- 401/403 authentication errors
- 500 server errors

Share the console errors for further diagnosis.

