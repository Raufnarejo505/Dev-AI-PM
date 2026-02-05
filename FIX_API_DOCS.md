# Fix API Documentation Error

## Problem
When accessing `/api/docs`, you see:
```
Unable to render this definition
The provided definition does not specify a valid version field.
```

## Solution
Added a custom OpenAPI schema function that explicitly sets the OpenAPI version to 3.1.0.

## Changes Made
- Updated `backend/app/main.py` to include a custom `openapi()` function
- Explicitly sets `openapi: "3.1.0"` in the schema
- Added proper description and metadata

## How to Apply

### On Your Server:

```bash
# 1. Rebuild backend container
docker compose -f docker-compose.prod.yml build backend

# 2. Restart backend
docker compose -f docker-compose.prod.yml restart backend

# 3. Wait a few seconds for backend to start
sleep 5

# 4. Test the OpenAPI schema
curl http://37.120.176.43:3000/api/openapi.json | head -20

# 5. Check if docs work
# Open in browser: http://37.120.176.43:3000/api/docs
```

## Verify Fix

1. **Check OpenAPI JSON**:
   ```bash
   curl http://37.120.176.43:3000/api/openapi.json | grep -A 2 "openapi"
   ```
   Should show: `"openapi": "3.1.0"`

2. **Access Swagger UI**:
   - URL: http://37.120.176.43:3000/api/docs
   - Should now load without errors

3. **Access ReDoc** (alternative):
   - URL: http://37.120.176.43:3000/api/redoc
   - Should also work

## Expected Result

After applying the fix:
- ✅ `/api/docs` loads successfully
- ✅ `/api/openapi.json` shows `"openapi": "3.1.0"`
- ✅ All API endpoints are visible in Swagger UI
- ✅ You can test endpoints directly from the docs

## Troubleshooting

### If still showing error:

1. **Check backend logs**:
   ```bash
   docker compose -f docker-compose.prod.yml logs backend | tail -50
   ```

2. **Verify OpenAPI schema**:
   ```bash
   curl http://37.120.176.43:3000/api/openapi.json | python -m json.tool | head -30
   ```

3. **Clear browser cache**:
   - Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

4. **Check if backend is running**:
   ```bash
   docker compose -f docker-compose.prod.yml ps backend
   ```

### If OpenAPI version is wrong:

The custom function should set it to 3.1.0. If you see a different version, check:
- Backend container was rebuilt
- Backend was restarted
- No caching issues

## Alternative: Use ReDoc

If Swagger UI still has issues, try ReDoc:
- URL: http://37.120.176.43:3000/api/redoc
- ReDoc is more lenient with OpenAPI versions



