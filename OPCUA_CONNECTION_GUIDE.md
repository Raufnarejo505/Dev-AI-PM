# OPC UA Connection Guide

## Quick Connection Steps

### 1. Access OPC UA Wizard
- Navigate to: **http://localhost:3000/opcua** (or your frontend URL)
- Or click "OPC UA" in the navigation menu

### 2. Configure Connection (Step 1: Basic Connection)
- **Endpoint URL**: `opc.tcp://DESKTOP-61HAQLS.mshome.net:53530/OPCUA/SimulationServer`
- **Namespace Index**: `3`
- **Sampling Interval**: `1000` (ms)
- **Session Timeout**: `60000` (ms)

### 3. Configure Security (Step 2: Security)
- Select: **Anonymous** (default for most simulators)
- If your server requires authentication, select "Username + Password" and enter credentials

### 4. Configure Nodes (Step 3: Nodes)
The following nodes are pre-configured:
- Temperature: `ns=3;i=1009` → alias: `opcua_temperature` → unit: `°C` → category: `temperature`
- Vibration: `ns=3;i=1010` → alias: `opcua_vibration` → unit: `mm/s` → category: `vibration`
- Motor Current: `ns=3;i=1012` → alias: `opcua_motor_current` → unit: `A` → category: `motor_current`
- Wear Index: `ns=3;i=1013` → alias: `opcua_wear_index` → unit: `%` → category: `wear`
- Pressure: `ns=3;i=1011` → alias: `opcua_pressure` → unit: `bar` → category: `pressure`

### 5. Test Connection (Step 6: Test + Activate)
- Click **"Test Connection"** button
- This will attempt to connect to your OPC UA server and read sample values
- Check the logs for connection status
- If successful, you'll see sample values from your nodes

### 6. Activate Source
- Click **"Activate Source"** button
- This will start the OPC UA connector and begin polling your server
- You should see a success message with the number of nodes activated

### 7. Verify Connection
- Go to Dashboard: **http://localhost:3000**
- Check the **"OPC UA Connection Status"** section at the bottom
- You should see:
  - Connection: **Connected** (green indicator)
  - Active Nodes: **5** (or number of configured nodes)
  - Active Sources: **1**
- The **Live Sensor Monitors** should start showing values from your OPC UA simulator

## Troubleshooting

### Connection Fails
1. **Check OPC UA Server is Running**
   - Verify your OPC UA simulator is running
   - Check the endpoint URL matches exactly

2. **Check Network Connectivity**
   - Try using IP address instead of hostname
   - Verify port 53530 is not blocked by firewall
   - Test connection from another OPC UA client first

3. **Check Endpoint URL Format**
   - Must start with `opc.tcp://`
   - Format: `opc.tcp://hostname:port/path`
   - Example: `opc.tcp://DESKTOP-61HAQLS.mshome.net:53530/OPCUA/SimulationServer`

4. **Check Node IDs**
   - Verify node IDs match your server's namespace
   - Format: `ns=3;i=1009` (namespace index = 3, node ID = 1009)
   - Use OPC UA client to browse and verify node IDs

5. **Check Backend Logs**
   ```bash
   docker-compose logs backend | grep -i opcua
   ```
   Look for connection errors or warnings

### Values Not Appearing
1. **Check OPC UA Status on Dashboard**
   - Verify connection shows "Connected"
   - Check for any error messages

2. **Check Sensor Monitors**
   - Values should update every 2 seconds
   - If showing 0 or "--", check if data is being ingested

3. **Check Backend Logs**
   ```bash
   docker-compose logs backend | grep -i "OPC UA"
   ```
   Look for polling messages and data ingestion

4. **Verify Node Configuration**
   - Ensure node IDs are correct
   - Check aliases match expected sensor types
   - Verify categories are set correctly

### Common Errors

**"Connection timeout"**
- Server is not reachable
- Firewall blocking connection
- Wrong endpoint URL

**"Name resolution failed"**
- Hostname cannot be resolved
- Try using IP address instead

**"Node not found"**
- Node ID is incorrect
- Namespace index is wrong
- Node doesn't exist on server

**"asyncua library not installed"**
- Backend needs asyncua package
- Check `backend/requirements.txt` includes `asyncua==1.1.0`
- Rebuild backend: `docker-compose build backend`

## Testing Connection via API

You can also test the connection directly via API:

```bash
# Login first
curl -X POST http://localhost:8000/users/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"

# Save the access_token, then test OPC UA connection
curl -X POST http://localhost:8000/opcua/test \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint_url": "opc.tcp://DESKTOP-61HAQLS.mshome.net:53530/OPCUA/SimulationServer",
    "namespace_index": 3,
    "sampling_interval_ms": 1000,
    "session_timeout_ms": 60000,
    "security_mode": "anonymous",
    "nodes": [
      {"node_id": "ns=3;i=1009", "alias": "opcua_temperature", "unit": "°C", "category": "temperature"}
    ]
  }'
```

## Expected Behavior

Once connected:
1. **Dashboard** shows live sensor values updating every 2-3 seconds
2. **Sensor Monitors** display Temperature, Vibration, Pressure, Motor Current, and Wear Index
3. **OPC UA Status** shows "Connected" with active node count
4. **Live Data Table** shows recent sensor readings
5. **Values change** when you modify them in the OPC UA simulator

## Next Steps

After successful connection:
- Monitor values on the dashboard
- Set up alarms based on thresholds
- View predictions generated from OPC UA data
- Generate reports with historical data
