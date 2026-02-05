# How to Disable Dummy Data and Focus on OPC UA Only

This guide shows you how to stop all dummy data sources so you can see only OPC UA data in the dashboard.

## ✅ Already Done (Code Changes)

I've already disabled:
1. ✅ **Live Data Generator** - Commented out in `backend/app/main.py`
2. ✅ **MQTT Consumer** - Commented out in `backend/app/main.py`

## 🔧 Additional Steps Required

### Step 1: Stop the MQTT Simulator Service

The simulator Docker container is still running and publishing dummy data. Stop it:

```bash
# Stop only the simulator service
docker-compose stop simulator

# Or remove it completely
docker-compose rm -f simulator
```

**Or edit `docker-compose.yml`** to comment out the simulator service:

```yaml
  # simulator:
  #   build:
  #     context: ./simulator
  #   depends_on:
  #     - mqtt
  #   environment:
  #     MQTT_BROKER_HOST: mqtt
  #     MQTT_BROKER_PORT: 1883
  #   networks:
  #     - pm-net
```

### Step 2: Restart Backend to Apply Changes

After making the code changes, restart the backend:

```bash
# Restart backend service
docker-compose restart backend

# Or rebuild if you modified docker-compose.yml
docker-compose up -d --build backend
```

### Step 3: Verify Dummy Data is Stopped

Check backend logs to confirm:

```bash
# Check backend logs
docker-compose logs backend | grep -i "live data\|mqtt\|generator"

# You should see:
# "⏸️  Live data generator DISABLED - only OPC UA data will be ingested"
# "⏸️  MQTT consumer DISABLED - only OPC UA data will be ingested"
```

### Step 4: Clear Existing Dummy Data (Optional)

If you want to remove existing dummy data from the database:

```bash
# Connect to database
docker-compose exec postgres psql -U pm_user -d pm_db

# Delete sensor data from dummy sources
DELETE FROM sensor_data WHERE metadata->>'generated_by' = 'live_data_generator';
DELETE FROM sensor_data WHERE metadata->>'source' != 'opcua';

# Delete predictions from dummy sources
DELETE FROM predictions WHERE metadata->>'generated_by' = 'live_data_generator';

# Exit
\q
```

## 🎯 Now Only OPC UA Data Will Appear

After these steps:
- ✅ No live data generator running
- ✅ No MQTT simulator publishing
- ✅ No MQTT consumer ingesting
- ✅ Only OPC UA connector is active

When you activate your OPC UA source, you'll see:
- Machine: `OPCUA-Simulation-Machine` (or whatever you set in tags)
- Sensors: `opcua_temperature`, `opcua_vibration`, `opcua_motor_current`, `opcua_wear_index`, `opcua_pressure`
- All sensor data will have `metadata->>'source' = 'opcua'`

## 🔍 Filter Dashboard by Source (Optional)

If you want to filter the dashboard to show only OPC UA data, you can modify the API calls in the frontend to filter by source. The sensor data has metadata indicating the source.

## 🔄 Re-enable Dummy Data Later

If you want to re-enable dummy data later:

1. **Uncomment in `backend/app/main.py`:**
   ```python
   # Re-enable live data generator
   from app.tasks.live_data_generator import start_live_data_generator
   loop.create_task(start_live_data_generator(interval_seconds=5))
   
   # Re-enable MQTT consumer
   mqtt_ingestor.start(loop)
   ```

2. **Start simulator:**
   ```bash
   docker-compose up -d simulator
   ```

3. **Restart backend:**
   ```bash
   docker-compose restart backend
   ```

---

## Quick Summary

```bash
# 1. Stop simulator
docker-compose stop simulator

# 2. Restart backend (code changes already applied)
docker-compose restart backend

# 3. Verify
docker-compose logs backend | grep -i "disabled"

# 4. Activate your OPC UA source and check dashboard!
```

Now your dashboard will show **only OPC UA data**! 🎉
