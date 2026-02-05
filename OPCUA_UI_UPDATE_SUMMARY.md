# OPC UA UI Update Summary

## ✅ Completed Changes

### 1. Simplified OPC UA Wizard
- **Location**: `frontend/src/pages/OPCUAWizard.tsx`
- **Changes**:
  - Removed complex multi-step wizard (6 steps → 1 simple form)
  - Now only requires:
    - **OPC UA Server URL** (simple text input)
    - **Variables/Nodes** (add/remove nodes with Node ID, Alias, Unit, Category, Min, Max)
  - Removed unnecessary security, payload, and routing configuration steps
  - Added real-time **Live Values** display with circle meters on the right side
  - Shows circle meters immediately after activation

### 2. Circle Meter Component
- **Location**: `frontend/src/components/CircleMeter.tsx`
- **Features**:
  - Beautiful circular gauge visualization
  - Shows value, unit, and status (normal/warning/critical)
  - Color-coded based on status:
    - 🟢 Normal: Cyan
    - 🟡 Warning: Amber
    - 🔴 Critical: Red
  - Configurable min/max ranges
  - Smooth animations and transitions
  - Responsive design

### 3. Updated Sensor Monitors
- **Location**: `frontend/src/components/SensorMonitors.tsx`
- **Changes**:
  - Now uses `CircleMeter` components instead of simple cards
  - Fixed API calls to use regular `api` instead of `safeApi`
  - Better error handling for authentication and network errors
  - Improved data mapping for OPC UA sensor aliases
  - Real-time updates every 2 seconds

### 4. Dashboard Integration
- **Location**: `frontend/src/pages/Dashboard.tsx`
- **Changes**:
  - Sensor Monitors section now displays circle meters
  - Values update in real-time as OPC UA simulator changes
  - Better visual feedback for sensor status

### 5. API Fixes
- **Location**: `frontend/src/components/SensorMonitors.tsx`
- **Changes**:
  - Fixed endpoint from `/sensor-data/logs?limit=50&sort=desc` to `/sensor-data/logs?limit=50`
  - Improved error handling for 401 (auth), 403 (permission), and 500 (server) errors
  - Better empty state messages

## 🎯 How to Use

### Step 1: Access OPC UA Wizard
1. Navigate to **http://localhost:3000/opcua**
2. Or click "OPC UA" in the navigation menu

### Step 2: Configure Connection
1. **Enter OPC UA Server URL**:
   ```
   opc.tcp://DESKTOP-61HAQLS.mshome.net:53530/OPCUA/SimulationServer
   ```

2. **Configure Variables/Nodes**:
   - Pre-filled with 5 default nodes:
     - Temperature: `ns=3;i=1009` → `opcua_temperature` (°C)
     - Vibration: `ns=3;i=1010` → `opcua_vibration` (mm/s)
     - Motor Current: `ns=3;i=1012` → `opcua_motor_current` (A)
     - Wear Index: `ns=3;i=1013` → `opcua_wear_index` (%)
     - Pressure: `ns=3;i=1011` → `opcua_pressure` (bar)
   - You can add/remove nodes as needed
   - Set Min/Max values for each node (used for gauge visualization)

### Step 3: Test Connection
1. Click **"Test Connection"** button
2. Wait for connection test results
3. Check logs for connection status

### Step 4: Activate Source
1. After successful test, click **"Activate & Start"**
2. Source will be activated and data collection starts
3. **Live Values** section will show circle meters with real-time data
4. Click **"Go to Dashboard →"** to view on main dashboard

### Step 5: View on Dashboard
1. Go to **Dashboard** (http://localhost:3000)
2. **Live Sensor Monitors** section shows all sensors as circle meters
3. Values update every 2 seconds automatically
4. Meters change color based on thresholds:
   - Normal: 0-70% of range
   - Warning: 70-90% of range
   - Critical: 90-100% of range

## 🔧 Technical Details

### Circle Meter Component
```typescript
<CircleMeter
  label="Temperature"
  value={75.5}
  unit="°C"
  min={0}
  max={100}
  status="warning"
  size={200}
/>
```

### API Endpoints Used
- `GET /sensor-data/logs?limit=50` - Fetch latest sensor data
- `POST /opcua/test` - Test OPC UA connection
- `POST /opcua/activate` - Activate OPC UA source
- `GET /opcua/status` - Get connection status

### Data Flow
1. OPC UA Connector polls nodes every 1 second (configurable)
2. Data is normalized and stored in `sensor_data` table
3. Frontend polls `/sensor-data/logs` every 2 seconds
4. Circle meters update with latest values
5. Status calculated based on min/max ranges

## 🐛 Troubleshooting

### "No live data available (Backend offline)"
- **Cause**: Authentication issue or backend not running
- **Fix**: 
  - Make sure you're logged in
  - Check backend is running: `docker-compose ps`
  - Verify OPC UA source is activated

### Circle meters show 0 or "--"
- **Cause**: No data being ingested from OPC UA
- **Fix**:
  - Check OPC UA simulator is running
  - Verify connection in OPC UA Wizard
  - Check backend logs: `docker-compose logs backend | findstr /i "opcua"`
  - Verify nodes are configured correctly

### Values not updating
- **Cause**: Frontend not polling or backend not writing data
- **Fix**:
  - Check browser console for errors
  - Verify API calls are successful (Network tab)
  - Check backend logs for OPC UA polling messages
  - Ensure OPC UA connector is running

### Authentication errors
- **Cause**: Token expired or missing
- **Fix**:
  - Log out and log back in
  - Check `localStorage.getItem('access_token')` in browser console
  - Verify backend JWT secret is configured

## 📊 Visual Features

### Circle Meters
- **Size**: 200px (configurable)
- **Colors**: 
  - Normal: Cyan (#22d3ee)
  - Warning: Amber (#f59e0b)
  - Critical: Red (#ef4444)
- **Animation**: Smooth transitions (500ms)
- **Status Badge**: Shows current status below value

### Layout
- **Wizard**: 2-column layout (Config | Live Values)
- **Dashboard**: 5-column grid for sensor monitors
- **Responsive**: Adapts to mobile/tablet/desktop

## 🚀 Next Steps

1. **Test the connection**:
   - Start OPC UA simulator
   - Configure connection in wizard
   - Activate source
   - Watch values update in real-time

2. **Customize thresholds**:
   - Adjust Min/Max values in wizard
   - Meters will reflect new ranges
   - Status colors update automatically

3. **Monitor on dashboard**:
   - All sensors displayed as circle meters
   - Real-time updates every 2 seconds
   - Color-coded status indicators

## 📝 Notes

- Circle meters require authentication (must be logged in)
- Values update every 2 seconds by default
- Status is calculated as percentage of min/max range
- OPC UA connector polls every 1 second (configurable)
- All data is stored in TimescaleDB for historical analysis
