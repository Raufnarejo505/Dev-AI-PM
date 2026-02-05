# OPC UA Setup Complete - Clean Configuration

## ✅ What Has Been Configured

### 1. OPC UA Wizard Pre-Configured
The frontend OPC UA wizard is now pre-filled with your exact server details:

- **Endpoint URL**: `opc.tcp://DESKTOP-61HAQLS:53530/OPCUA/SimulationServer`
- **Namespace Index**: `3`
- **Security Mode**: `anonymous` (already set)
- **All 5 Nodes Pre-Configured**:
  - Temperature: `ns=3;i=1009` → `opcua_temperature` (°C)
  - Vibration: `ns=3;i=1010` → `opcua_vibration` (mm/s)
  - MotorCurrent: `ns=3;i=1012` → `opcua_motor_current` (A)
  - WearIndex: `ns=3;i=1013` → `opcua_wear_index` (%)
  - Pressure: `ns=3;i=1011` → `opcua_pressure` (bar)
- **Machine Tag**: `OPCUA-Simulation-Machine`

### 2. All Dummy Data Sources Disabled

✅ **Live Data Generator** - Disabled  
✅ **MQTT Consumer** - Disabled  
✅ **MQTT Simulator** - Disabled in docker-compose.yml  
✅ **Demo Machines Seeding** - Disabled  

### 3. What's Still Active (Required)

✅ **Demo Users** - Kept for login (admin@example.com, etc.)  
✅ **OPC UA Connector** - Active and ready  
✅ **Database** - Ready for OPC UA data only  

---

## 🚀 Quick Start Guide

### Step 1: Start Services (Without Simulator)

```bash
# Start all services except simulator
docker-compose up -d postgres mqtt ai-service backend frontend

# Or if you want to be explicit:
docker-compose up -d --scale simulator=0
```

### Step 2: Access OPC UA Wizard

1. Open http://localhost:3000
2. Login with `admin@example.com` / `admin123`
3. Navigate to **OPC UA** page (from sidebar)
4. You'll see the wizard **already pre-filled** with your server details!

### Step 3: Review and Activate

The wizard is pre-configured, but you can review:

- **Step 1 (Basic Connection)**: 
  - Endpoint: `opc.tcp://DESKTOP-61HAQLS:53530/OPCUA/SimulationServer`
  - Namespace: `3`
  - ✅ Already correct!

- **Step 2 (Security)**: 
  - Mode: `anonymous`
  - ✅ Already correct!

- **Step 3 (Nodes)**: 
  - All 5 nodes are already added
  - ✅ Ready to go!

- **Step 5 (Routing)**: 
  - Machine tag: `OPCUA-Simulation-Machine`
  - ✅ Already set!

- **Step 6 (Test + Activate)**:
  - Click **"Test Connection"** to verify
  - Click **"Activate Source"** to start ingesting data

### Step 4: Verify Data Flow

After activation, check:

```bash
# Check OPC UA status
curl http://localhost:8000/opcua/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check sensor data (should only show OPC UA data)
curl "http://localhost:8000/sensor-data/logs?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Or in the frontend:
- **Dashboard** → Should show only OPC UA data
- **Machines** → Should show `OPCUA-Simulation-Machine`
- **Sensors** → Should show 5 OPC UA sensors

---

## 🎯 What You'll See

### Machines
- **Name**: `OPCUA-Simulation-Machine`
- **Source**: Created automatically from OPC UA tags
- **Status**: `online` (when OPC UA is connected)

### Sensors (Auto-Created)
1. `opcua_temperature` (°C)
2. `opcua_vibration` (mm/s)
3. `opcua_motor_current` (A)
4. `opcua_wear_index` (%)
5. `opcua_pressure` (bar)

### Data Flow
```
OPC UA Simulator Server
    ↓ (every 1 second)
Backend OPC UA Connector
    ↓
TimescaleDB (sensor_data table)
    ↓
AI Service (anomaly detection)
    ↓
Dashboard (real-time visualization)
```

---

## 🔍 Verify Everything is Clean

### Check Backend Logs

```bash
docker-compose logs backend | grep -i "disabled\|opcua"
```

You should see:
- `⏸️  Live data generator DISABLED`
- `⏸️  MQTT consumer DISABLED`
- `⏸️  Demo machines DISABLED`
- `OPC UA connector worker started`

### Check No Dummy Data

```bash
# Connect to database
docker-compose exec postgres psql -U pm_user -d pm_db

# Check sensor data sources
SELECT DISTINCT metadata->>'source', COUNT(*) 
FROM sensor_data 
GROUP BY metadata->>'source';

# Should only show 'opcua' after you activate
# Exit with \q
```

---

## 🛠️ Troubleshooting

### OPC UA Connection Fails

1. **Verify server is running**:
   - Check that your OPC UA Simulation Server is running on `DESKTOP-61HAQLS:53530`
   - Test with an OPC UA client tool (UaExpert) to confirm connectivity

2. **Check network**:
   ```bash
   # From backend container
   docker-compose exec backend ping DESKTOP-61HAQLS
   ```

3. **Check backend logs**:
   ```bash
   docker-compose logs -f backend | grep -i opcua
   ```

### No Data Appearing

1. **Wait a few seconds** - Polling happens every 1 second
2. **Check OPC UA status**:
   ```bash
   curl http://localhost:8000/opcua/status \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```
   - Should show `connected: true`
   - Should show `node_count: 5`

3. **Verify nodes are correct**:
   - Double-check node IDs match your simulator exactly
   - Check namespace index is `3`

---

## 📝 Summary

✅ **Wizard Pre-Configured** - Your server details are already filled in  
✅ **All Dummy Data Disabled** - Clean slate for OPC UA only  
✅ **Ready to Connect** - Just click "Activate Source" in the wizard  
✅ **Direct Sync** - Data flows directly from OPC UA → Database → Dashboard  

**Next Step**: Open the OPC UA wizard, review the pre-filled settings, and click "Activate Source"! 🎉
