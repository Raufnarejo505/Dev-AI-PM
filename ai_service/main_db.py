"""
AI Service with direct database connection
Processes sensor data directly from TimescaleDB without MQTT
"""

import asyncio
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from scipy import stats
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from loguru import logger

# Database configuration
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@postgres:5432/predictive_maintenance"

# ==================== CONFIGURATION ====================
MODEL_DIR = Path(__file__).resolve().parent / "models"
WINDOW_SIZE = 60
MIN_SAMPLES = 12
BUFFER_CLEANUP_MINUTES = 120  # Clean buffers older than 2 hours

# Industrial stability controls (reduce flapping)
EMA_ALPHA = 0.2  # smoothing factor for anomaly score
MIN_STATUS_DWELL_SECONDS = 30  # minimum time to keep a status before downgrading
HYSTERESIS = {
    "warning_enter": 0.75,
    "warning_exit": 0.60,
    "critical_enter": 0.92,
    "critical_exit": 0.80,
}

DEFAULT_THRESHOLDS = {
    "pressure": {"warn": 150.0, "alarm": 180.0},
    "temperature": {"warn": 250.0, "alarm": 280.0},
    "vibration": {"warn": 4.0, "alarm": 6.0},
    "motor_current": {"warn": 18.0, "alarm": 22.0},
}

# ==================== DATA MODELS ====================
class APIModel(BaseModel):
    model_config = {"protected_namespaces": ()}

class PredictPayload(APIModel):
    machine_id: str
    sensor_id: str
    timestamp: datetime
    readings: Dict[str, float] = Field(default_factory=dict)

class PredictionResponse(APIModel):
    machine_id: str
    sensor_id: str
    timestamp: datetime
    anomaly_score: float
    status: str
    features: Dict[str, float] = Field(default_factory=dict)
    model_version: str = "1.0"

class HealthResponse(APIModel):
    status: str
    timestamp: datetime
    models_loaded: int
    active_buffers: int
    uptime_seconds: float

# ==================== DATABASE SETUP ====================
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ==================== AI MODEL ====================
@dataclass
class PerformanceTracker:
    """Track model performance and calibration"""
    total_predictions: int = 0
    anomaly_count: int = 0
    last_calibration: Optional[datetime] = None
    drift_detected: bool = False

class AnomalyDetector:
    """Isolation Forest-based anomaly detection with industrial controls"""
    
    def __init__(self):
        self.models: Dict[str, Any] = {}  # sensor_id -> model
        self.buffers: Dict[str, Deque[Dict[str, float]]] = defaultdict(lambda: deque(maxlen=WINDOW_SIZE))
        self.performance: Dict[str, PerformanceTracker] = defaultdict(PerformanceTracker)
        self.ema_scores: Dict[str, float] = {}  # Exponential moving average of anomaly scores
        self.status_history: Dict[str, Deque[tuple]] = defaultdict(lambda: deque(maxlen=10))
        self.last_cleanup = time.time()
        self.start_time = time.time()
        self._lock = threading.Lock()
        
        # Load existing models
        self._load_models()

    def _load_models(self):
        """Load pre-trained models from disk"""
        MODEL_DIR.mkdir(exist_ok=True)
        for model_file in MODEL_DIR.glob("*.joblib"):
            sensor_id = model_file.stem
            try:
                self.models[sensor_id] = joblib.load(model_file)
                logger.info(f"Loaded model for sensor {sensor_id}")
            except Exception as e:
                logger.error(f"Failed to load model {sensor_id}: {e}")

    def _save_model(self, sensor_id: str, model: Any):
        """Save model to disk"""
        try:
            model_path = MODEL_DIR / f"{sensor_id}.joblib"
            joblib.dump(model, model_path)
            logger.info(f"Saved model for sensor {sensor_id}")
        except Exception as e:
            logger.error(f"Failed to save model {sensor_id}: {e}")

    def _extract_features(self, readings: Dict[str, float]) -> np.ndarray:
        """Extract statistical features from sensor readings"""
        features = []
        
        # Basic statistics
        values = list(readings.values())
        if values:
            features.extend([
                np.mean(values),
                np.std(values),
                np.min(values),
                np.max(values),
                np.median(values)
            ])
            
            # Percentiles
            features.extend(np.percentile(values, [25, 75]))
            
            # Range and variance
            features.extend([
                np.max(values) - np.min(values),
                np.var(values)
            ])
            
            # Trend (last vs first)
            if len(values) > 1:
                features.append(values[-1] - values[0])
            else:
                features.append(0.0)
        else:
            # Default features if no data
            features = [0.0] * 11
            
        return np.array(features).reshape(1, -1)

    def _update_ema(self, sensor_id: str, score: float) -> float:
        """Update exponential moving average of anomaly score"""
        if sensor_id not in self.ema_scores:
            self.ema_scores[sensor_id] = score
        else:
            self.ema_scores[sensor_id] = (
                EMA_ALPHA * score + 
                (1 - EMA_ALPHA) * self.ema_scores[sensor_id]
            )
        return self.ema_scores[sensor_id]

    def _apply_hysteresis(self, sensor_id: str, ema_score: float) -> str:
        """Apply hysteresis to prevent status flapping"""
        history = self.status_history[sensor_id]
        current_time = time.time()
        
        # Remove old entries
        history.extend([(ema_score, current_time)] for _ in range(1))
        history = deque([x for x in history if current_time - x[1] < MIN_STATUS_DWELL_SECONDS], maxlen=10)
        self.status_history[sensor_id] = history
        
        if not history:
            return "normal"
            
        avg_score = np.mean([x[0] for x in history])
        
        # Apply hysteresis thresholds
        if avg_score >= HYSTERESIS["critical_enter"]:
            return "critical"
        elif avg_score >= HYSTERESIS["warning_enter"]:
            return "warning"
        elif avg_score >= HYSTERESIS["warning_exit"]:
            return "warning"
        else:
            return "normal"

    def predict(self, payload: PredictPayload) -> PredictionResponse:
        """Make prediction for sensor data"""
        with self._lock:
            sensor_id = payload.sensor_id
            timestamp = payload.timestamp
            
            # Update buffer
            self.buffers[sensor_id].extend(payload.readings.items())
            
            # Clean old buffers
            if time.time() - self.last_cleanup > BUFFER_CLEANUP_MINUTES * 60:
                self._cleanup_buffers()
                self.last_cleanup = time.time()
            
            # Check if we have enough data
            buffer_data = list(self.buffers[sensor_id])
            if len(buffer_data) < MIN_SAMPLES:
                return PredictionResponse(
                    machine_id=payload.machine_id,
                    sensor_id=sensor_id,
                    timestamp=timestamp,
                    anomaly_score=0.0,
                    status="insufficient_data",
                    model_version="1.0"
                )
            
            # Extract features
            readings_dict = dict(buffer_data[-WINDOW_SIZE:])
            features = self._extract_features(readings_dict)
            
            # Get or train model
            if sensor_id not in self.models:
                self.models[sensor_id] = self._train_model(sensor_id, buffer_data)
            
            model = self.models[sensor_id]
            
            # Make prediction
            try:
                anomaly_score = float(model.decision_function(features)[0])
                # Convert to positive anomaly score (higher = more anomalous)
                anomaly_score = -anomaly_score if anomaly_score < 0 else anomaly_score
                anomaly_score = max(0, min(1, anomaly_score))  # Normalize to [0,1]
            except Exception as e:
                logger.error(f"Prediction failed for {sensor_id}: {e}")
                anomaly_score = 0.0
            
            # Apply EMA smoothing
            ema_score = self._update_ema(sensor_id, anomaly_score)
            
            # Apply hysteresis
            status = self._apply_hysteresis(sensor_id, ema_score)
            
            # Update performance tracking
            perf = self.performance[sensor_id]
            perf.total_predictions += 1
            if status in ["warning", "critical"]:
                perf.anomaly_count += 1
            
            return PredictionResponse(
                machine_id=payload.machine_id,
                sensor_id=sensor_id,
                timestamp=timestamp,
                anomaly_score=anomaly_score,
                status=status,
                features={"feature_" + str(i): float(features[0, i]) for i in range(features.shape[1])},
                model_version="1.0"
            )

    def _train_model(self, sensor_id: str, buffer_data: List[tuple]) -> Any:
        """Train isolation forest model on buffer data"""
        try:
            from sklearn.ensemble import IsolationForest
            
            # Prepare training data
            readings_dict = dict(buffer_data)
            features = self._extract_features(readings_dict)
            
            # Train model
            model = IsolationForest(
                n_estimators=100,
                contamination=0.1,
                random_state=42,
                n_jobs=-1
            )
            
            # For single sample, create synthetic data
            if len(features) == 1:
                synthetic_data = np.repeat(features, 20, axis=0)
                # Add some noise
                noise = np.random.normal(0, 0.1, synthetic_data.shape)
                synthetic_data += noise
                model.fit(synthetic_data)
            else:
                model.fit(features)
            
            # Save model
            self._save_model(sensor_id, model)
            
            logger.info(f"Trained new model for sensor {sensor_id}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to train model for {sensor_id}: {e}")
            # Return dummy model
            from sklearn.ensemble import IsolationForest
            dummy_data = np.random.rand(20, 11)
            return IsolationForest().fit(dummy_data)

    def _cleanup_buffers(self):
        """Clean old buffer data"""
        current_time = time.time()
        cutoff_time = current_time - (BUFFER_CLEANUP_MINUTES * 60)
        
        for sensor_id in list(self.buffers.keys()):
            buffer = self.buffers[sensor_id]
            if len(buffer) == 0:
                continue
                
            # Remove old entries (this is approximate since we don't store timestamps in buffer)
            # For now, just clear buffers that haven't been updated recently
            if sensor_id not in self.performance or self.performance[sensor_id].total_predictions == 0:
                self.buffers[sensor_id].clear()

    def get_health(self) -> HealthResponse:
        """Get service health status"""
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            models_loaded=len(self.models),
            active_buffers=len([b for b in self.buffers.values() if len(b) > 0]),
            uptime_seconds=time.time() - self.start_time
        )

# ==================== FASTAPI APP ====================
app = FastAPI(title="AI Anomaly Detection Service", version="1.0.0")
detector = AnomalyDetector()

@app.post("/predict", response_model=PredictionResponse)
async def predict(payload: PredictPayload):
    """Make anomaly prediction for sensor data"""
    try:
        return detector.predict(payload)
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=HealthResponse)
async def health():
    """Service health check"""
    return detector.get_health()

@app.get("/models")
async def list_models():
    """List loaded models"""
    return {
        "models": list(detector.models.keys()),
        "count": len(detector.models)
    }

# ==================== DATABASE POLLING ====================
async def poll_sensor_data():
    """Poll database for new sensor data and process it"""
    while True:
        try:
            async with async_session() as session:
                # Get latest sensor data from last 5 seconds
                five_seconds_ago = datetime.utcnow() - timedelta(seconds=5)
                
                # Query sensor data
                from app.models.sensor_data import SensorData
                result = await session.execute(
                    select(SensorData)
                    .where(SensorData.timestamp >= five_seconds_ago)
                    .order_by(SensorData.timestamp.desc())
                    .limit(100)
                )
                
                sensor_data_list = result.scalars().all()
                
                # Group by sensor for processing
                sensor_groups = defaultdict(list)
                for data in sensor_data_list:
                    sensor_groups[data.sensor_id].append(data)
                
                # Process each sensor's data
                for sensor_id, data_list in sensor_groups.items():
                    if data_list:
                        # Get the latest reading
                        latest = data_list[0]
                        
                        # Create prediction payload
                        payload = PredictPayload(
                            machine_id=latest.machine_id,
                            sensor_id=sensor_id,
                            timestamp=latest.timestamp,
                            readings={"value": latest.value}
                        )
                        
                        # Make prediction
                        prediction = detector.predict(payload)
                        
                        # Store prediction in database (optional)
                        # This would require the prediction model to be available
                        # For now, we just log it
                        logger.info(f"AI prediction for {sensor_id}: {prediction.status} (score: {prediction.anomaly_score:.3f})")
                
        except Exception as e:
            logger.error(f"Error polling sensor data: {e}")
        
        # Wait before next poll
        await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    """Start database polling"""
    logger.info("Starting AI service with direct database connection")
    asyncio.create_task(poll_sensor_data())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
