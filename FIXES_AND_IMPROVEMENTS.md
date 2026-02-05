# Fixes and Improvements Summary

## ✅ Issues Fixed

### 1. **All 4 Machines Now Show in Dashboard**

**Problem**: Only 2 machines (Pump-01, Motor-02) were showing, but simulator has 4 machines.

**Solution**:
- Updated `backend/app/tasks/seed_demo_data.py` to create all 4 machines:
  - Pump-01 (Building A, Floor 2)
  - Motor-02 (Building B, Floor 1)
  - Compressor-A (Building C, Floor 3)
  - Conveyor-B2 (Building B, Floor 2)
- Each machine now has 4 sensors matching the simulator configuration
- Updated `backend/app/main.py` to automatically seed machines on startup

**To Apply**:
```bash
# Restart backend to auto-seed machines
docker compose -f docker-compose.prod.yml restart backend

# Or manually run seed script
docker compose -f docker-compose.prod.yml exec backend python -m app.tasks.seed_demo_data
```

### 2. **Fixed "Offline Mode" Issue**

**Problem**: Dashboard showed "Offline Mode" even when backend was running.

**Solution**:
- Updated `frontend/src/store/backendStore.ts` to use `API_BASE_URL` from `frontend/src/api/index.ts`
- This ensures consistent API URL resolution (uses `/api` in production)
- Exported `API_BASE_URL` from `frontend/src/api/index.ts` for reuse

**Result**: Dashboard now correctly shows "Online" when backend is accessible.

### 3. **AI Live Predictions**

**Status**: AI predictions should work automatically when:
- Simulator is running and publishing data
- Backend is ingesting MQTT messages
- AI service is processing sensor data

**To Verify**:
1. Start simulator: `docker compose -f docker-compose.prod.yml up -d simulator`
2. Wait 1-2 minutes for data to accumulate
3. Check Predictions page: http://37.120.176.43:3000/predictions
4. Check Dashboard: Should show AI predictions count

## 📋 Complete Service & Endpoint List

Created `ALL_SERVICES_ENDPOINTS.md` with:
- All service URLs and ports
- Complete backend API endpoint list
- AI service endpoints
- MQTT topics
- Quick access commands

## 🚀 Quick Commands

### Start Simulator
```bash
docker compose -f docker-compose.prod.yml up -d simulator
```

### Seed All Machines
```bash
docker compose -f docker-compose.prod.yml exec backend python -m app.tasks.seed_demo_data
```

### Check Services
```bash
# Backend health
curl http://37.120.176.43:3000/api/health

# Backend status
curl http://37.120.176.43:3000/api/status

# AI status
curl http://37.120.176.43:3000/api/ai/status

# MQTT status
curl http://37.120.176.43:3000/api/mqtt/status
```

### View Logs
```bash
# Simulator logs
docker compose -f docker-compose.prod.yml logs simulator -f

# Backend logs
docker compose -f docker-compose.prod.yml logs backend -f

# AI service logs
docker compose -f docker-compose.prod.yml logs ai-service -f
```

## 📊 Expected Results

After applying fixes:

1. **Dashboard** (http://37.120.176.43:3000):
   - ✅ Shows "Online" (not "Offline Mode")
   - ✅ Shows all 4 machines
   - ✅ Shows AI predictions count
   - ✅ Shows live sensor data

2. **Machines Page** (http://37.120.176.43:3000/machines):
   - ✅ Shows 4 machines:
     - Pump-01
     - Motor-02
     - Compressor-A
     - Conveyor-B2

3. **Sensors Page** (http://37.120.176.43:3000/sensors):
   - ✅ Shows sensors from all 4 machines
   - ✅ Live data updates every few seconds

4. **Predictions Page** (http://37.120.176.43:3000/predictions):
   - ✅ Shows AI predictions
   - ✅ Shows anomaly scores
   - ✅ Updates with new predictions

## 🔧 Files Modified

1. `backend/app/tasks/seed_demo_data.py` - Added all 4 machines
2. `backend/app/main.py` - Auto-seed machines on startup
3. `frontend/src/store/backendStore.ts` - Fixed offline mode detection
4. `frontend/src/api/index.ts` - Exported API_BASE_URL

## 📝 New Documentation

1. `ALL_SERVICES_ENDPOINTS.md` - Complete service and endpoint reference
2. `SEED_ALL_MACHINES.md` - Instructions for seeding machines
3. `HOW_TO_RUN_SIMULATOR.md` - Simulator usage guide
4. `FIXES_AND_IMPROVEMENTS.md` - This file

## 🎯 Next Steps

1. **Restart backend** to auto-seed all machines:
   ```bash
   docker compose -f docker-compose.prod.yml restart backend
   ```

2. **Start simulator** (if not running):
   ```bash
   docker compose -f docker-compose.prod.yml up -d simulator
   ```

3. **Wait 1-2 minutes** for data to populate

4. **Check dashboard** - Should show all 4 machines and live data

5. **Verify AI predictions** - Check Predictions page

## 🐛 Troubleshooting

### Still showing only 2 machines?
```bash
# Manually seed machines
docker compose -f docker-compose.prod.yml exec backend python -m app.tasks.seed_demo_data

# Check machines in database
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "SELECT name FROM machines;"
```

### Still showing "Offline Mode"?
```bash
# Check backend health
curl http://37.120.176.43:3000/api/health/live

# Check backend logs
docker compose -f docker-compose.prod.yml logs backend | tail -50

# Restart frontend
docker compose -f docker-compose.prod.yml restart frontend
```

### No AI predictions?
```bash
# Check AI service status
curl http://37.120.176.43:3000/api/ai/status

# Check if simulator is running
docker compose -f docker-compose.prod.yml ps simulator

# Check sensor data exists
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "SELECT COUNT(*) FROM sensor_data;"
```



