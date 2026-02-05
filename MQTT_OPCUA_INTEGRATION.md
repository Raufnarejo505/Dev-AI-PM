# MQTT Integration with OPC UA Edge Gateway

## Overview

The backend MQTT consumer is now configured to receive data from the OPC UA Edge Gateway and process it into the database.

## Data Flow

```
Prosys OPC UA Simulator Server
  ↓ [OPC UA Subscriptions]
OPC UA → MQTT Gateway (edge-gateway)
  ↓ [MQTT QoS 1]
MQTT Broker (factory/extruder-01/telemetry)
  ↓ [MQTT Subscribe]
Backend MQTT Consumer
  ↓ [Process & Store]
Database (TimescaleDB)
```

## Configuration

### MQTT Topics

The backend subscribes to:
- `factory/+/telemetry` - OPC UA edge gateway messages
- `edge/#` - Edge device messages
- `sensors/+/telemetry` - Legacy sensor format

### Message Format from Edge Gateway

The edge gateway publishes messages in this format:

```json
{
  "timestamp": "2026-01-08T09:15:32.421Z",
  "machineId": "extruder-01",
  "profile": 1,
  "temperature": 187.2,
  "vibration": 2.9,
  "pressure": 132.5,
  "motorCurrent": 14.1,
  "wearIndex": 18.4
}
```

### Processing Logic

The MQTT consumer:
1. **Receives** message on `factory/{machineId}/telemetry`
2. **Splits** into individual sensor messages:
   - `opcua_temperature` → Temperature value
   - `opcua_vibration` → Vibration value
   - `opcua_pressure` → Pressure value
   - `opcua_motor_current` → Motor Current value
   - `opcua_wear_index` → Wear Index value
3. **Auto-creates** machine if not exists (from `machineId`)
4. **Auto-creates** sensors if not exists (from sensor names)
5. **Stores** each sensor reading in database

## Status

### Check MQTT Connection

```bash
# Check backend logs
docker-compose logs backend | grep -i "mqtt"

# Check MQTT status via API
curl http://localhost:8000/api/mqtt/status
```

You should see:
- `"connected": true`
- Topics subscribed: `["factory/+/telemetry", "edge/#", "sensors/+/telemetry"]`

### Verify Data Ingestion

```bash
# Check backend logs for MQTT messages
docker-compose logs -f backend | grep -i "mqtt\|received\|ingested"

# You should see:
# ✅ MQTT connected successfully
# 📨 Received OPC UA edge gateway message
# ✅ Queued sensor data
# Sensor data ingested
```

## Starting the Pipeline

### 1. Start All Services

```bash
# Start MQTT broker
docker-compose up -d mqtt

# Start OPC UA edge gateway
docker-compose up -d edge-gateway

# Start backend (with MQTT consumer enabled)
docker-compose up -d backend
```

### 2. Verify Connections

```bash
# Check edge gateway logs
docker-compose logs -f edge-gateway

# Check backend MQTT consumer logs
docker-compose logs -f backend | grep -i mqtt
```

### 3. Monitor Data Flow

```bash
# Watch backend process messages
docker-compose logs -f backend | grep -E "Received|ingested|Processing"
```

## Troubleshooting

### MQTT Shows "Disconnected"

**Check:**
1. Is MQTT broker running? `docker-compose ps mqtt`
2. Is backend MQTT consumer enabled? Check `backend/app/main.py`
3. Check backend logs: `docker-compose logs backend | grep -i mqtt`

**Fix:**
```bash
# Restart backend
docker-compose restart backend

# Check logs
docker-compose logs -f backend
```

### No Messages Received

**Check:**
1. Is edge gateway running? `docker-compose ps edge-gateway`
2. Is edge gateway publishing? Check logs: `docker-compose logs edge-gateway`
3. Are topics correct? Backend should subscribe to `factory/+/telemetry`

**Fix:**
```bash
# Restart edge gateway
docker-compose restart edge-gateway

# Check MQTT broker for messages
docker-compose exec mqtt mosquitto_sub -t "factory/+/telemetry" -v
```

### Messages Received But Not Stored

**Check:**
1. Check backend logs for errors: `docker-compose logs backend | grep -i error`
2. Verify database connection: `docker-compose logs backend | grep -i database`
3. Check sensor/machine creation: `docker-compose logs backend | grep -i "Auto-registering"`

## Dummy Data Removal

All dummy data sources have been disabled:
- ✅ Live data generator - DISABLED
- ✅ MQTT simulator - DISABLED (if it was running)
- ✅ Demo machines seeding - DISABLED

Only real data from OPC UA (via edge gateway) will be ingested.

## Next Steps

1. **Start the edge gateway** to begin publishing OPC UA data
2. **Verify MQTT connection** in backend logs
3. **Check dashboard** to see real-time sensor data
4. **Monitor logs** to ensure data is flowing correctly

## Summary

✅ MQTT consumer is **ENABLED** and configured to receive from edge gateway
✅ Topics configured: `factory/+/telemetry`
✅ Message format handler implemented for edge gateway payload
✅ Auto-registration of machines and sensors
✅ Dummy data generators disabled

The system is now ready to receive real OPC UA data via MQTT!
