# OPC UA AI Integration - Complete

## ✅ Integration Complete

AI processing has been fully integrated into the OPC UA connector. Now when OPC UA data is ingested, it automatically:

1. **Stores sensor data** in the database
2. **Calls AI service** for anomaly detection and predictions
3. **Stores predictions** with scores, confidence, and anomaly types
4. **Creates alarms** automatically when anomalies are detected
5. **Sends notifications** for critical/warning predictions
6. **Triggers webhooks** for critical alarms
7. **Broadcasts real-time updates** via WebSocket

## Data Flow

```
OPC UA Simulator Server
  ↓ [Reads sensor values]
OPC UA Connector
  ↓ [Stores in database]
Sensor Data Table
  ↓ [Calls AI Service]
AI Service (Isolation Forest)
  ↓ [Returns prediction]
Prediction Table
  ↓ [If anomaly detected]
Alarm Table
  ↓ [If critical]
Notifications + Webhooks
```

## What Happens for Each Sensor Reading

### 1. Data Ingestion
- OPC UA connector reads value from simulator
- Stores in `sensor_data` table
- Machine: `OPCUA-Simulation-Machine` (auto-created)
- Sensor: Auto-created based on node alias

### 2. AI Processing
- Sensor reading sent to AI service: `POST /predict`
- AI service buffers readings (sliding window of 60 samples)
- Once buffer has 12+ samples, makes prediction
- Returns:
  - `prediction`: "normal" or "anomaly"
  - `status`: "normal", "warning", "critical", or "buffering"
  - `score`: 0.0 (normal) to 1.0 (critical)
  - `confidence`: 0.0 to 1.0
  - `anomaly_type`: "NORMAL", "WARNING", "CRITICAL", or "BASELINE"
  - `rul`: Remaining Useful Life (0-100%)

### 3. Prediction Storage
- Prediction stored in `prediction` table
- Includes all AI service response data
- Metadata includes source: "opcua"

### 4. Alarm Creation
- If `status` is "warning" or "critical":
  - Creates alarm in `alarm` table
  - Severity: "warning" or "critical"
  - Links to prediction and sensor

### 5. Notifications
- Email sent for critical/warning predictions (if configured)
- Webhooks triggered for critical alarms (if configured)
- Real-time updates broadcast via WebSocket

### 6. Fallback
- Rule-based threshold alarms still run as backup
- Works even if AI service is unavailable

## Sensor Name Mapping

OPC UA sensor aliases are mapped to AI service expected names:

| OPC UA Alias | AI Service Name |
|--------------|-----------------|
| `temperature` | `temperature` |
| `vibration` | `vibration` |
| `pressure` | `pressure` |
| `motorCurrent` | `motor_current` |
| `wearIndex` | `wear_index` |

## AI Service Configuration

- **Model**: Isolation Forest (scikit-learn)
- **Location**: `http://ai-service:8000`
- **Endpoint**: `POST /predict`
- **Buffer Size**: 60 samples per sensor
- **Min Samples**: 12 (before making predictions)
- **Fallback**: Rule-based threshold detection

## Viewing Predictions

### Dashboard
- Predictions appear in the Dashboard
- Shows anomaly scores, confidence, and status
- Updates in real-time

### Predictions Page
- View all predictions: `/predictions`
- Filter by machine, sensor, status
- See prediction history

### Alarms Page
- View alarms created from AI predictions: `/alarms`
- See severity, message, and linked prediction

## Monitoring

### Check AI Service Status
```bash
curl http://localhost:8000/api/ai/status
```

### Check Predictions
```bash
curl http://localhost:8000/api/predictions?limit=10
```

### Check Alarms
```bash
curl http://localhost:8000/api/alarms?status=active
```

## Logs

### Backend Logs
```bash
docker-compose logs backend | grep -i "prediction\|ai"
```

You should see:
- `✅ AI Prediction created: machine=..., sensor=..., status=..., score=...`
- `🚨 Alarm created: machine=..., sensor=..., severity=...`

### AI Service Logs
```bash
docker-compose logs ai-service | grep -i "predict"
```

## Performance

- **AI Response Time**: Typically 10-20ms per prediction
- **Processing**: Each sensor reading triggers AI call
- **Buffering**: AI service buffers readings for better accuracy
- **Throughput**: Handles multiple concurrent predictions

## Summary

✅ **AI Processing**: Fully integrated
✅ **Predictions**: Stored automatically
✅ **Alarms**: Created for anomalies
✅ **Notifications**: Sent for critical events
✅ **Real-time Updates**: Broadcast via WebSocket
✅ **Fallback**: Rule-based alarms as backup

The OPC UA simulator data now flows through the complete AI-powered predictive maintenance pipeline!
