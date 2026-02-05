# Quick Start - OPC UA Only Setup

## ✅ Everything is Pre-Configured!

Your system is now configured to connect **directly to your OPC UA Simulator Server** with all dummy data removed.

---

## 🚀 3 Simple Steps

### Step 1: Start Services

```bash
# Start all services (simulator is already disabled)
docker-compose up -d

# Or if simulator was running before, stop it:
docker-compose stop simulator
```

### Step 2: Open OPC UA Wizard

1. Go to http://localhost:3000
2. Login: `admin@example.com` / `admin123`
3. Click **"OPC UA"** in the sidebar

### Step 3: Activate!

The wizard is **already pre-filled** with:
- ✅ Your server: `opc.tcp://DESKTOP-61HAQLS:53530/OPCUA/SimulationServer`
- ✅ Namespace: `3`
- ✅ Security: `anonymous`
- ✅ All 5 nodes configured
- ✅ Machine name: `OPCUA-Simulation-Machine`

**Just click "Test Connection" then "Activate Source"!**

---

## 📊 What Happens Next

1. **Backend connects** to your OPC UA server every 1 second
2. **Reads all 5 nodes**: Temperature, Vibration, MotorCurrent, WearIndex, Pressure
3. **Auto-creates**:
   - Machine: `OPCUA-Simulation-Machine`
   - 5 Sensors (one for each node)
4. **Stores data** in database
5. **Shows in dashboard** in real-time

---

## 🎯 Verify It's Working

### Check Status
```bash
curl http://localhost:8000/opcua/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Should show:
- `connected: true`
- `node_count: 5`
- `active: true` for your source

### Check Dashboard
- Open http://localhost:3000
- Go to **Dashboard** → Should show only OPC UA data
- Go to **Machines** → Should see `OPCUA-Simulation-Machine`
- Go to **Sensors** → Should see 5 OPC UA sensors

---

## ✨ That's It!

Your system is now **100% focused on OPC UA** with:
- ✅ No dummy data
- ✅ No MQTT simulator
- ✅ No demo machines
- ✅ Direct sync with your OPC UA server

**Just activate the source in the wizard and you're done!** 🎉
