# Fix Offline Mode - Rebuild Frontend

## Problem
Backend is working, but frontend shows "Offline Mode" because the health check is using wrong API URL.

## Solution: Rebuild Frontend with Correct Configuration

### Step 1: Rebuild frontend container

```bash
docker compose -f docker-compose.prod.yml build frontend
```

### Step 2: Restart frontend

```bash
docker compose -f docker-compose.prod.yml up -d frontend
```

### Step 3: Wait a few seconds

```bash
sleep 5
```

### Step 4: Test from browser

1. Open browser: http://37.120.176.43:3000
2. Open browser console (F12)
3. Check Network tab for `/api/health/live` requests
4. Should see 200 OK responses

### Step 5: Hard refresh browser

- Press `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- This clears cache and reloads the page

## Alternative: Quick Test Without Rebuild

Test if the issue is just browser cache:

1. Open browser console (F12)
2. Go to Application tab → Clear Storage → Clear site data
3. Reload page (F5)

## Expected Results

✅ Frontend rebuilt with correct API URL  
✅ Health check succeeds  
✅ Dashboard shows "Backend: Online"  
✅ "Offline Mode" banner disappears  
✅ Live updates work

## If Still Not Working

Check browser console (F12) for:
- Network errors
- CORS errors
- Failed `/api/health/live` requests

Share the console errors for further diagnosis.

