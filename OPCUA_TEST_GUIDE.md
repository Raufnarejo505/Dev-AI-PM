# OPC UA Integration Test Guide

## Your OPC UA Server Configuration

- **Endpoint URL**: `opc.tcp://DESKTOP-61HAQLS:53530/OPCUA/SimulationServer`
- **Security Mode**: Anonymous (default)
- **Namespace Index**: 3

## Configured Nodes

| Sensor | Node ID | Alias | Unit | Category |
|--------|---------|-------|------|----------|
| Temperature | `ns=3;i=1009` | `opcua_temperature` | `°C` | `temperature` |
| Vibration | `ns=3;i=1010` | `opcua_vibration` | `mm/s` | `vibration` |
| MotorCurrent | `ns=3;i=1012` | `opcua_motor_current` | `A` | `motor_current` |
| WearIndex | `ns=3;i=1013` | `opcua_wear_index` | `%` | `wear` |
| Pressure | `ns=3;i=1011` | `opcua_pressure` | `bar` | `pressure` |

---

## Step-by-Step Testing

### Step 1: Ensure Backend is Running

```bash
# Check backend health
curl http://localhost:8000/health

# Expected: {"status":"ok",...}
```

### Step 2: Login and Get JWT Token

```bash
# Login as admin
curl -X POST http://localhost:8000/users/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"

# Save the access_token from the response
# Example response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "refresh_token": "...",
#   "token_type": "bearer"
# }
```

**Set your token as an environment variable (PowerShell):**
```powershell
$TOKEN = "YOUR_ACCESS_TOKEN_HERE"
```

**Or for bash:**
```bash
export TOKEN="YOUR_ACCESS_TOKEN_HERE"
```

### Step 3: Test OPC UA Configuration

This validates the configuration without actually connecting:

```powershell
# PowerShell
$headers = @{
    "Authorization" = "Bearer $TOKEN"
    "Content-Type" = "application/json"
}

$body = @{
    name = "OPC UA Simulation Server"
    endpoint_url = "opc.tcp://DESKTOP-61HAQLS:53530/OPCUA/SimulationServer"
    namespace_index = 3
    sampling_interval_ms = 1000
    session_timeout_ms = 60000
    security_mode = "anonymous"
    timestamp_source = "server"
    tags = @{
        machine = "OPCUA-Simulation-Machine"
    }
    nodes = @(
        @{
            node_id = "ns=3;i=1009"
            alias = "opcua_temperature"
            unit = "°C"
            category = "temperature"
        },
        @{
            node_id = "ns=3;i=1010"
            alias = "opcua_vibration"
            unit = "mm/s"
            category = "vibration"
        },
        @{
            node_id = "ns=3;i=1012"
            alias = "opcua_motor_current"
            unit = "A"
            category = "motor_current"
        },
        @{
            node_id = "ns=3;i=1013"
            alias = "opcua_wear_index"
            unit = "%"
            category = "wear"
        },
        @{
            node_id = "ns=3;i=1011"
            alias = "opcua_pressure"
            unit = "bar"
            category = "pressure"
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:8000/opcua/test" -Method POST -Headers $headers -Body $body
```

**Or using curl (Windows/Linux/Mac):**
```bash
curl -X POST http://localhost:8000/opcua/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OPC UA Simulation Server",
    "endpoint_url": "opc.tcp://DESKTOP-61HAQLS:53530/OPCUA/SimulationServer",
    "namespace_index": 3,
    "sampling_interval_ms": 1000,
    "session_timeout_ms": 60000,
    "security_mode": "anonymous",
    "timestamp_source": "server",
    "tags": {
      "machine": "OPCUA-Simulation-Machine"
    },
    "nodes": [
      {
        "node_id": "ns=3;i=1009",
        "alias": "opcua_temperature",
        "unit": "°C",
        "category": "temperature"
      },
      {
        "node_id": "ns=3;i=1010",
        "alias": "opcua_vibration",
        "unit": "mm/s",
        "category": "vibration"
      },
      {
        "node_id": "ns=3;i=1012",
        "alias": "opcua_motor_current",
        "unit": "A",
        "category": "motor_current"
      },
      {
        "node_id": "ns=3;i=1013",
        "alias": "opcua_wear_index",
        "unit": "%",
        "category": "wear"
      },
      {
        "node_id": "ns=3;i=1011",
        "alias": "opcua_pressure",
        "unit": "bar",
        "category": "pressure"
      }
    ]
  }'
```

**Expected Response:**
```json
{
  "ok": true,
  "handshake_logs": [
    "Preparing OPC UA test to opc.tcp://DESKTOP-61HAQLS:53530/OPCUA/SimulationServer",
    "Configuration payload validated successfully."
  ],
  "sample_preview": [...]
}
```

### Step 4: Activate OPC UA Source

This actually registers the source and starts polling:

```bash
curl -X POST http://localhost:8000/opcua/activate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OPC UA Simulation Server",
    "endpoint_url": "opc.tcp://DESKTOP-61HAQLS:53530/OPCUA/SimulationServer",
    "namespace_index": 3,
    "sampling_interval_ms": 1000,
    "session_timeout_ms": 60000,
    "security_mode": "anonymous",
    "timestamp_source": "server",
    "tags": {
      "machine": "OPCUA-Simulation-Machine"
    },
    "nodes": [
      {
        "node_id": "ns=3;i=1009",
        "alias": "opcua_temperature",
        "unit": "°C",
        "category": "temperature"
      },
      {
        "node_id": "ns=3;i=1010",
        "alias": "opcua_vibration",
        "unit": "mm/s",
        "category": "vibration"
      },
      {
        "node_id": "ns=3;i=1012",
        "alias": "opcua_motor_current",
        "unit": "A",
        "category": "motor_current"
      },
      {
        "node_id": "ns=3;i=1013",
        "alias": "opcua_wear_index",
        "unit": "%",
        "category": "wear"
      },
      {
        "node_id": "ns=3;i=1011",
        "alias": "opcua_pressure",
        "unit": "bar",
        "category": "pressure"
      }
    ]
  }'
```

**Expected Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "OPC UA Simulation Server",
  "node_count": 5
}
```

### Step 5: Check OPC UA Status

```bash
curl http://localhost:8000/opcua/status \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response (after a few seconds):**
```json
{
  "connected": true,
  "heartbeat_ts": 1234567890.123,
  "node_count": 5,
  "last_error": null,
  "sources": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "OPC UA Simulation Server",
      "endpoint_url": "opc.tcp://DESKTOP-61HAQLS:53530/OPCUA/SimulationServer",
      "active": true,
      "node_count": 5
    }
  ]
}
```

### Step 6: Verify Data is Being Ingested

**Check sensor data logs:**
```bash
curl "http://localhost:8000/sensor-data/logs?limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

**Check machines:**
```bash
curl "http://localhost:8000/machines" \
  -H "Authorization: Bearer $TOKEN"
```

You should see a machine named `OPCUA-Simulation-Machine`.

**Check sensors:**
```bash
curl "http://localhost:8000/sensors" \
  -H "Authorization: Bearer $TOKEN"
```

You should see sensors:
- `opcua_temperature`
- `opcua_vibration`
- `opcua_motor_current`
- `opcua_wear_index`
- `opcua_pressure`

### Step 7: View in Frontend Dashboard

1. Open http://localhost:3000
2. Login with `admin@example.com` / `admin123`
3. Navigate to **Machines** page
4. Look for `OPCUA-Simulation-Machine`
5. Navigate to **Sensors** page
6. You should see all 5 OPC UA sensors with live data
7. Navigate to **Dashboard** to see real-time updates

---

## Troubleshooting

### Connection Errors

If `last_error` in `/opcua/status` shows connection issues:

1. **Verify OPC UA server is running:**
   - Check that your OPC UA Simulation Server is running on `DESKTOP-61HAQLS:53530`
   - Test with an OPC UA client tool (e.g., UaExpert) to confirm connectivity

2. **Check network connectivity:**
   ```bash
   # Test if the endpoint is reachable (if using Docker, test from inside container)
   docker-compose exec backend ping DESKTOP-61HAQLS
   ```

3. **Verify security mode:**
   - If your server requires authentication, update `security_mode` to `"username_password"` and provide `username`/`password` in the config

4. **Check backend logs:**
   ```bash
   docker-compose logs backend | grep -i opcua
   # Or if running locally:
   # Check console output for OPC UA errors
   ```

### No Data Appearing

1. **Wait a few seconds:** The connector polls every `sampling_interval_ms` (1000ms = 1 second)
2. **Check status:** Ensure `connected: true` and `node_count: 5` in `/opcua/status`
3. **Verify node IDs:** Double-check that your node IDs match exactly what your simulator exposes
4. **Check backend logs for errors:**
   ```bash
   docker-compose logs -f backend
   ```

### Node ID Format

The connector expects node IDs in the format:
- `ns=3;i=1009` (numeric identifier)
- `ns=3;s=StringIdentifier` (string identifier)

Your node IDs (`ns=3;i=1009`, etc.) are correct!

---

## Quick Test Script (PowerShell)

Save this as `test-opcua.ps1`:

```powershell
# OPC UA Test Script
$BASE_URL = "http://localhost:8000"
$ENDPOINT = "opc.tcp://DESKTOP-61HAQLS:53530/OPCUA/SimulationServer"

# Step 1: Login
Write-Host "Step 1: Logging in..." -ForegroundColor Cyan
$loginResponse = Invoke-RestMethod -Uri "$BASE_URL/users/login" -Method POST `
    -Headers @{"Content-Type"="application/x-www-form-urlencoded"} `
    -Body "username=admin@example.com&password=admin123"
$TOKEN = $loginResponse.access_token
Write-Host "✓ Login successful" -ForegroundColor Green

# Step 2: Test configuration
Write-Host "`nStep 2: Testing OPC UA configuration..." -ForegroundColor Cyan
$headers = @{
    "Authorization" = "Bearer $TOKEN"
    "Content-Type" = "application/json"
}
$config = @{
    name = "OPC UA Simulation Server"
    endpoint_url = $ENDPOINT
    namespace_index = 3
    sampling_interval_ms = 1000
    security_mode = "anonymous"
    tags = @{ machine = "OPCUA-Simulation-Machine" }
    nodes = @(
        @{ node_id = "ns=3;i=1009"; alias = "opcua_temperature"; unit = "°C"; category = "temperature" }
        @{ node_id = "ns=3;i=1010"; alias = "opcua_vibration"; unit = "mm/s"; category = "vibration" }
        @{ node_id = "ns=3;i=1012"; alias = "opcua_motor_current"; unit = "A"; category = "motor_current" }
        @{ node_id = "ns=3;i=1013"; alias = "opcua_wear_index"; unit = "%"; category = "wear" }
        @{ node_id = "ns=3;i=1011"; alias = "opcua_pressure"; unit = "bar"; category = "pressure" }
    )
} | ConvertTo-Json -Depth 10

$testResponse = Invoke-RestMethod -Uri "$BASE_URL/opcua/test" -Method POST -Headers $headers -Body $config
Write-Host "✓ Configuration test: $($testResponse.ok)" -ForegroundColor Green

# Step 3: Activate
Write-Host "`nStep 3: Activating OPC UA source..." -ForegroundColor Cyan
$activateResponse = Invoke-RestMethod -Uri "$BASE_URL/opcua/activate" -Method POST -Headers $headers -Body $config
Write-Host "✓ Source activated: $($activateResponse.id)" -ForegroundColor Green
Write-Host "  Node count: $($activateResponse.node_count)" -ForegroundColor Yellow

# Step 4: Wait and check status
Write-Host "`nStep 4: Waiting 3 seconds for first poll..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

$statusResponse = Invoke-RestMethod -Uri "$BASE_URL/opcua/status" -Method GET -Headers $headers
Write-Host "✓ Status check:" -ForegroundColor Green
Write-Host "  Connected: $($statusResponse.connected)" -ForegroundColor $(if ($statusResponse.connected) { "Green" } else { "Red" })
Write-Host "  Node count: $($statusResponse.node_count)" -ForegroundColor Yellow
if ($statusResponse.last_error) {
    Write-Host "  Last error: $($statusResponse.last_error)" -ForegroundColor Red
}

# Step 5: Check sensor data
Write-Host "`nStep 5: Checking sensor data..." -ForegroundColor Cyan
$sensorData = Invoke-RestMethod -Uri "$BASE_URL/sensor-data/logs?limit=10" -Method GET -Headers $headers
Write-Host "✓ Found $($sensorData.items.Count) recent sensor data entries" -ForegroundColor Green

Write-Host "`n✓ OPC UA integration test complete!" -ForegroundColor Green
```

Run it:
```powershell
.\test-opcua.ps1
```

---

## Summary

✅ **Endpoint**: `opc.tcp://DESKTOP-61HAQLS:53530/OPCUA/SimulationServer`  
✅ **5 Nodes configured**: Temperature, Vibration, MotorCurrent, WearIndex, Pressure  
✅ **Data flow**: OPC UA Server → Backend Connector → Database → Frontend Dashboard  
✅ **Automatic**: Machine and sensors are auto-created, alarms trigger if thresholds exceeded

Once activated, the backend will poll your OPC UA server every second and ingest all 5 sensor values into the predictive maintenance platform!
