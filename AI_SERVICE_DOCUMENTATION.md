# AI Service Documentation

## Overview

The Predictive Maintenance platform uses an **AI Anomaly Detection Service** that processes sensor data to identify anomalies, predict failures, and provide maintenance recommendations.

## AI Model Used

### Primary Model: **Isolation Forest**

- **Algorithm**: Isolation Forest (scikit-learn)
- **Type**: Unsupervised anomaly detection
- **Purpose**: Detects anomalies in sensor readings without requiring labeled training data
- **Location**: `ai_service/models/isolation_forest.pkl`

### Fallback: Rule-Based Engine

- **When Used**: If ML model is not available or fails to load
- **Method**: Threshold-based rules for sensor values
- **Thresholds**:
  ```python
  {
    "pressure": {"warn": 150.0, "alarm": 180.0},
    "temperature": {"warn": 250.0, "alarm": 280.0},
    "vibration": {"warn": 4.0, "alarm": 6.0},
    "motor_current": {"warn": 18.0, "alarm": 22.0}
  }
  ```

## AI Service Architecture

### Service Location
- **Service Name**: `ai-service`
- **Port**: `8000` (internal), `8001` (external)
- **URL**: `http://ai-service:8000` (Docker) or `http://localhost:8001` (external)
- **Technology**: FastAPI (Python)

### Key Components

1. **PredictionEngine** (`ai_service/main.py`)
   - Manages sensor data buffers (sliding window)
   - Extracts features from sensor readings
   - Runs Isolation Forest model
   - Falls back to rule-based detection if model unavailable

2. **FeatureEngineer** (`ai_service/main.py`)
   - Extracts 25 statistical features from sensor data
   - Features include: mean, std, min, max, median, trend, z-scores, correlations
   - Transforms raw sensor readings into model-ready format

3. **PerformanceTracker**
   - Monitors prediction performance
   - Tracks response times
   - Provides metrics for monitoring

## API Endpoints

### 1. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_version": "1.0.0",
  "buffers": 5,
  "performance": {
    "predictions_total": 1000,
    "predictions_per_second": 2.5,
    "avg_response_time_ms": 15.3
  },
  "system_metrics": {
    "memory_usage_mb": 128.5,
    "cpu_percent": 5.2,
    "active_buffers": 5
  }
}
```

### 2. Predict Anomaly
```http
POST /predict
Content-Type: application/json
```

**Request Body:**
```json
{
  "machine_id": "extruder-01",
  "sensor_id": "opcua_temperature",
  "timestamp": "2026-01-08T10:30:00Z",
  "readings": {
    "temperature": 187.2,
    "vibration": 2.9,
    "pressure": 132.5,
    "motor_current": 14.1
  }
}
```

**Response:**
```json
{
  "prediction": "anomaly",
  "status": "warning",
  "score": 0.75,
  "confidence": 0.85,
  "anomaly_type": "WARNING",
  "model_version": "1.0.0",
  "rul": 25.0,
  "response_time_ms": 12.5,
  "contributing_features": {
    "rule_score": 0.7,
    "model_score": 0.75,
    "window_size": 45,
    "buffer_utilization": 0.75
  }
}
```

**Response Fields:**
- `prediction`: "normal" or "anomaly"
- `status`: "normal", "warning", "critical", or "buffering"
- `score`: Anomaly score (0.0 = normal, 1.0 = critical)
- `confidence`: Prediction confidence (0.0 - 1.0)
- `anomaly_type`: "NORMAL", "WARNING", "CRITICAL", or "BASELINE"
- `rul`: Remaining Useful Life (0-100%)
- `response_time_ms`: API response time in milliseconds

### 3. System Status
```http
GET /system/status
```

**Response:**
```json
{
  "service": "AI Anomaly Detection",
  "status": "operational",
  "timestamp": "2026-01-08T10:30:00Z",
  "model": {
    "loaded": true,
    "version": "1.0.0",
    "type": "Isolation Forest + Rule Engine"
  },
  "buffers": {
    "active": 5,
    "total_entries": 225,
    "window_size": 60,
    "min_samples": 12
  },
  "performance": {...},
  "system": {...}
}
```

### 4. Metrics
```http
GET /metrics
```

**Response:**
```json
{
  "predictions_total": 1000,
  "predictions_per_second": 2.5,
  "avg_response_time_ms": 15.3,
  "active_buffers": 5,
  "memory_usage_mb": 128.5
}
```

## How Backend Uses AI Service

### 1. MQTT Consumer Integration

When sensor data arrives via MQTT, the backend:

1. **Stores sensor data** in database
2. **Calls AI service** to get prediction:
   ```python
   POST http://ai-service:8000/predict
   {
     "machine_id": "extruder-01",
     "sensor_id": "opcua_temperature",
     "timestamp": "...",
     "readings": {
       "temperature": 187.2,
       "vibration": 2.9,
       ...
     }
   }
   ```
3. **Stores prediction** in database
4. **Creates alarms** if status is "warning" or "critical"
5. **Sends notifications** if configured

**Location**: `backend/app/mqtt/consumer.py` (lines 400-570)

### 2. OPC UA Connector Integration

Similar flow when data comes from OPC UA:
- Data ingested → AI service called → Predictions stored

**Location**: `backend/app/opcua/connector.py`

### 3. Direct API Calls

Backend provides API endpoints to trigger predictions:

**Location**: `backend/app/api/routers/predictions.py`

## Data Flow

```
Sensor Data (MQTT/OPC UA)
  ↓
Backend MQTT Consumer / OPC UA Connector
  ↓
Store in Database (sensor_data table)
  ↓
Call AI Service API: POST /predict
  ↓
AI Service:
  - Buffers sensor data (sliding window)
  - Extracts 25 features
  - Runs Isolation Forest model
  - Returns prediction
  ↓
Backend:
  - Stores prediction in database
  - Creates alarms if needed
  - Sends notifications
  ↓
Frontend displays predictions and alarms
```

## Feature Engineering

The AI service extracts **25 features** from sensor data:

1. **Statistical Features** (8):
   - Mean, Standard Deviation, Min, Max, Median
   - Skewness, Kurtosis, IQR (Interquartile Range)

2. **Trend Analysis** (4):
   - Linear slope, Intercept
   - Short vs Long moving average difference
   - Short/Long MA ratio

3. **Pattern Detection** (3):
   - Z-score (standardized deviation)
   - Rate of change
   - Optimal deviation

4. **Correlation Features** (2):
   - Lag-1 autocorrelation
   - 1 - |autocorrelation|

5. **Additional Features** (8):
   - Buffer utilization
   - Window size
   - Other derived metrics

## Configuration

### Environment Variables

**Backend** (`backend/.env`):
```bash
AI_SERVICE_URL=http://ai-service:8000
```

**AI Service** (`ai_service/.env`):
```bash
# Model directory
MODEL_DIR=./models

# Buffer settings
WINDOW_SIZE=60
MIN_SAMPLES=12
```

### Model Files

Located in `ai_service/models/`:
- `isolation_forest.pkl` - Trained Isolation Forest model
- `scaler.pkl` - Feature scaler (StandardScaler)
- `metadata.json` - Model metadata and version info

## Monitoring

### Health Checks

Backend checks AI service health:
```http
GET /api/ai/status
```

### Metrics

View AI service metrics:
```http
GET http://ai-service:8000/metrics
```

### Logs

Check AI service logs:
```bash
docker-compose logs ai-service
```

## Performance

- **Response Time**: Typically 10-20ms per prediction
- **Throughput**: Handles multiple concurrent requests
- **Memory**: ~100-200MB per service instance
- **Buffers**: Maintains sliding window (60 samples) per sensor

## Fallback Behavior

If AI service is unavailable:
1. Backend logs warning
2. Predictions are not generated
3. Rule-based alarms still work (threshold-based)
4. System continues operating normally

## Training the Model

To train/retrain the model:

1. **Prepare training data**: `ai_service/data/training_data.csv`
2. **Run training script**: `python ai_service/train_model.py`
3. **Model saved to**: `ai_service/models/isolation_forest.pkl`
4. **Restart AI service**: `docker-compose restart ai-service`

## Summary

- **AI Model**: Isolation Forest (scikit-learn)
- **API**: FastAPI REST service at `http://ai-service:8000`
- **Main Endpoint**: `POST /predict`
- **Features**: 25 statistical features extracted from sensor data
- **Fallback**: Rule-based threshold detection
- **Integration**: Called automatically by backend when sensor data arrives

The AI service is a critical component that provides intelligent anomaly detection and predictive maintenance capabilities to the platform.
