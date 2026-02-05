# OPC UA Implementation Flow - How It Connects to Simulator Server

## Overview

This document explains how the Predictive Maintenance application connects to the OPC UA Simulator Server and displays real-time data in the dashboard.

## Architecture Diagram

```
┌─────────────────────────┐
│  OPC UA Simulator       │
│  Server                 │
│  (Port 53530)           │
│  - Temperature          │
│  - Vibration            │
│  - Pressure             │
│  - Motor Current        │
│  - Wear Index           │
└───────────┬─────────────┘
            │
            │ OPC UA Protocol
            │ (opc.tcp://...)
            │
            ▼
┌─────────────────────────┐
│  Backend Application    │
│  (FastAPI)              │
│                         │
│  ┌───────────────────┐  │
│  │ OPC UA Connector │  │
│  │ - Polls every 1s │  │
│  │ - Reads nodes     │  │
│  │ - Normalizes data │  │
│  └─────────┬─────────┘  │
│            │            │
│            ▼            │
│  ┌───────────────────┐  │
│  │ Data Ingestion     │  │
│  │ - Creates machines │  │
│  │ - Creates sensors  │  │
│  │ - Stores data      │  │
│  └─────────┬─────────┘  │
└────────────┼────────────┘
             │
             │ Database
             │ (TimescaleDB)
             ▼
┌─────────────────────────┐
│  PostgreSQL/TimescaleDB │
│  - sensor_data table    │
│  - sensor table         │
│  - machine table        │
└───────────┬─────────────┘
            │
            │ REST API
            │ (GET /sensor-data/logs)
            ▼
┌─────────────────────────┐
│  Frontend Application   │
│  (React)                │
│                         │
│  ┌───────────────────┐  │
│  │ Dashboard         │  │
│  │ - Fetches data    │  │
│  │ - Every 2 seconds │  │
│  └─────────┬─────────┘  │
│            │            │
│            ▼            │
│  ┌───────────────────┐  │
│  │ Circle Meters      │  │
│  │ - Displays values  │  │
│  │ - Updates live     │  │
│  └───────────────────┘  │
└─────────────────────────┘
```

## Step-by-Step Data Flow

### 1. **OPC UA Simulator Server**
- **Location**: Runs on `opc.tcp://DESKTOP-61HAQLS.mshome.net:53530/OPCUA/SimulationServer`
- **Purpose**: Simulates industrial sensors with changing values
- **Nodes Available**:
  - `ns=3;i=1009` → Temperature (°C)
  - `ns=3;i=1010` → Vibration (mm/s)
  - `ns=3;i=1011` → Pressure (bar)
  - `ns=3;i=1012` → Motor Current (A)
  - `ns=3;i=1013` → Wear Index (%)

### 2. **Configuration (OPC UA Wizard)**
- **Location**: `frontend/src/pages/OPCUAWizard.tsx`
- **User Action**: 
  1. Enter OPC UA server URL
  2. Configure nodes (Node ID, Alias, Unit, Category)
  3. Click "Test Connection" → Validates connection
  4. Click "Activate & Start" → Starts data collection

### 3. **Backend Activation**
- **Location**: `backend/app/api/routers/opcua.py`
- **Endpoint**: `POST /opcua/activate`
- **What Happens**:
  ```python
  # Registers OPC UA source in memory
  source = OPCUASourceConfig(
      endpoint_url="opc.tcp://...",
      nodes=[...],
      active=True
  )
  registry.upsert(source)
  registry.mark_active(source.id, True)
  ```

### 4. **OPC UA Connector Worker**
- **Location**: `backend/app/opcua/connector.py`
- **Started**: Automatically on backend startup
- **How It Works**:
  ```python
  async def _run(self):
      while self._running:
          for source in active_sources:
              await self._poll_source_once(source)
          await asyncio.sleep(1)  # Poll every 1 second
  ```

### 5. **Polling Process**
- **Location**: `backend/app/opcua/connector.py` → `_poll_source_once()`
- **Steps**:
  1. **Connect** to OPC UA server using `asyncua.Client`
  2. **Read each node**:
     ```python
     node = client.get_node("ns=3;i=1009")
     value = await node.read_value()
     ```
  3. **Normalize data**:
     ```python
     sample = normalize_opcua_sample(
         alias="opcua_temperature",
         value=175.93,
         unit="°C",
         timestamp=datetime.now()
     )
     ```
  4. **Route to database**:
     ```python
     await self._route_sample(source, node_cfg, sample)
     ```

### 6. **Data Ingestion**
- **Location**: `backend/app/opcua/connector.py` → `_route_sample()`
- **Process**:
  1. **Auto-create Machine** (if doesn't exist):
     ```python
     machine = await machine_service.get_machine(session, "OPCUA-Simulation-Machine")
     if not machine:
         machine = await machine_service.create_machine(...)
     ```
  2. **Auto-create Sensor** (if doesn't exist):
     ```python
     sensor = await sensor_service.get_sensor(session, "opcua_temperature")
     if not sensor:
         sensor = await sensor_service.create_sensor(...)
     ```
  3. **Store Sensor Data**:
     ```python
     await sensor_data_service.ingest_sensor_data(
         session,
         SensorDataIn(
             sensor_id=sensor.id,
             machine_id=machine.id,
             value=175.93,
             timestamp=datetime.now(),
             metadata={"alias": "opcua_temperature", "unit": "°C"}
         )
     )
     ```

### 7. **Database Storage**
- **Table**: `sensor_data`
- **Columns**:
  - `id` (BigInteger)
  - `sensor_id` (UUID)
  - `machine_id` (UUID)
  - `timestamp` (DateTime)
  - `value` (Numeric)
  - `status` (String)
  - `metadata` (JSON) - Contains alias, unit, source info

### 8. **Frontend Data Fetching**
- **Location**: `frontend/src/components/SensorMonitors.tsx`
- **Process**:
  ```typescript
  useEffect(() => {
      const fetchSensorData = async () => {
          const response = await api.get('/sensor-data/logs?limit=50');
          // Process and display data
      };
      fetchSensorData();
      const interval = setInterval(fetchSensorData, 2000); // Every 2 seconds
  }, []);
  ```

### 9. **Data Display**
- **Location**: `frontend/src/components/CircleMeter.tsx`
- **Process**:
  1. Frontend receives sensor data from API
  2. Maps data to monitor types (temperature, vibration, etc.)
  3. Calculates percentage for gauge display
  4. Updates circle meters with new values
  5. Shows status (normal/warning/critical)

## Key Components

### Backend Components

1. **OPC UA Connector** (`backend/app/opcua/connector.py`)
   - Long-running worker that polls OPC UA servers
   - Handles connection, reading, and error recovery
   - Runs continuously in background

2. **Source Registry** (`backend/app/opcua/source_registry.py`)
   - In-memory registry of active OPC UA sources
   - Manages source configuration and activation state

3. **Schema Normalizer** (`backend/app/opcua/schema_normalizer.py`)
   - Converts raw OPC UA values to standardized format
   - Handles timestamps, units, and quality codes

4. **API Router** (`backend/app/api/routers/opcua.py`)
   - `/opcua/test` - Tests connection to OPC UA server
   - `/opcua/activate` - Activates a source and starts polling
   - `/opcua/status` - Returns connection status and node count

### Frontend Components

1. **OPC UA Wizard** (`frontend/src/pages/OPCUAWizard.tsx`)
   - Configuration interface for OPC UA connection
   - Tests connection before activation
   - Shows live values after activation

2. **Sensor Monitors** (`frontend/src/components/SensorMonitors.tsx`)
   - Fetches latest sensor data every 2 seconds
   - Maps OPC UA aliases to monitor types
   - Displays circle meters for each sensor

3. **Circle Meter** (`frontend/src/components/CircleMeter.tsx`)
   - Visual gauge component
   - Shows value, unit, and status
   - Updates in real-time

## Data Mapping

### OPC UA Node → Database → Frontend

```
OPC UA Simulator
  ↓
Node: ns=3;i=1009
Value: 175.93
  ↓
Backend Normalization
  ↓
{
  "alias": "opcua_temperature",
  "value": 175.93,
  "unit": "°C",
  "timestamp": "2026-01-08T07:53:05Z"
}
  ↓
Database (sensor_data table)
  ↓
API Response
  ↓
Frontend Mapping
  ↓
Circle Meter Display
  - Label: "TEMPERATURE"
  - Value: 175.93
  - Unit: "°C"
  - Status: "NORMAL"
```

## Real-Time Updates

### Update Frequency

1. **OPC UA Polling**: Every 1 second (configurable)
   - Backend reads from simulator
   - Stores in database

2. **Frontend Polling**: Every 2 seconds
   - Fetches latest data from API
   - Updates circle meters

3. **Visual Updates**: Instant
   - Circle meters animate smoothly
   - Status colors update based on thresholds

## Connection Status

### How to Check Connection

1. **Dashboard**: Shows OPC UA Connection Status card
   - Connection: Connected/Disconnected
   - Active Nodes: Number of nodes being polled
   - Active Sources: Number of configured sources

2. **Backend Logs**:
   ```bash
   docker-compose logs backend | grep -i "opcua"
   ```
   - Shows connection attempts
   - Shows polling success/failures
   - Shows data ingestion

3. **API Endpoint**: `GET /opcua/status`
   - Returns heartbeat timestamp
   - Returns node count
   - Returns last error (if any)

## Troubleshooting

### If Values Don't Update

1. **Check OPC UA Simulator**:
   - Is it running?
   - Is the endpoint URL correct?
   - Are the node IDs correct?

2. **Check Backend Connection**:
   - Look for connection errors in logs
   - Verify source is activated
   - Check `/opcua/status` endpoint

3. **Check Data Ingestion**:
   - Verify data is being stored in database
   - Check `sensor_data` table for recent entries
   - Verify sensor aliases match frontend mapping

4. **Check Frontend**:
   - Verify API calls are successful (Network tab)
   - Check browser console for errors
   - Verify authentication token is valid

## Summary

The OPC UA implementation creates a complete data pipeline:

1. **Simulator** generates sensor values
2. **Backend Connector** polls and reads values
3. **Database** stores historical data
4. **API** serves data to frontend
5. **Frontend** displays in real-time circle meters

All components work together to provide real-time monitoring of OPC UA simulator data with automatic updates every 1-2 seconds.
