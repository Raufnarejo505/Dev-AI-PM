# Quick Fix: Run on Port 3000 Instead of 80

## ✅ Solution: Use Port 3000

I've already updated your `docker-compose.prod.yml` to use port 3000 instead of 80.

## Commands to Run on Server

```bash
# 1. Navigate to project directory
cd "/root/Predictive Maintenance"

# 2. Restart frontend with new port
docker compose -f docker-compose.prod.yml up -d frontend

# 3. Check if it's running
docker compose -f docker-compose.prod.yml ps

# 4. Test the application
curl http://localhost:3000/health
```

## Access Your Application

After restarting, access at:
- **Frontend**: http://37.120.176.43:3000
- **Backend API**: http://37.120.176.43:3000/api
- **API Docs**: http://37.120.176.43:3000/api/docs
- **Health Check**: http://37.120.176.43:3000/health

## Benefits

✅ **No conflict** - Both projects can run simultaneously
✅ **No disruption** - Other person's project keeps running on port 80
✅ **Easy access** - Just add :3000 to the URL
✅ **Safe** - No need to stop anyone else's services

## Alternative Ports

If port 3000 is also taken, you can use:
- `8080:80` → Access at http://37.120.176.43:8080
- `3001:80` → Access at http://37.120.176.43:3001
- `5000:80` → Access at http://37.120.176.43:5000

Just change the port number in `docker-compose.prod.yml` and restart.

---

**Note**: The configuration file has been updated. Just restart the frontend container on your server!

