from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from scipy import stats

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

class PredictResponse(APIModel):
    prediction: str
    status: str
    score: float
    confidence: float
    anomaly_type: str
    model_version: str
    rul: Optional[float] = None
    response_time_ms: float
    contributing_features: Dict[str, Any] = Field(default_factory=dict)

class HealthResponse(APIModel):
    status: str
    model_loaded: bool
    model_version: str
    buffers: int
    performance: Dict[str, float]
    system_metrics: Dict[str, Any]

class MetricsResponse(APIModel):
    predictions_total: int
    predictions_per_second: float
    avg_response_time_ms: float
    active_buffers: int
    memory_usage_mb: float

# ==================== PERFORMANCE TRACKER ====================
class PerformanceTracker:
    def __init__(self, window_size: int = 1000):
        self.response_times: Deque[float] = deque(maxlen=window_size)
        self.prediction_count = 0
        self._lock = threading.RLock()
    
    @contextmanager
    def track_prediction(self):
        start_time = time.perf_counter()
        yield
        duration = time.perf_counter() - start_time
        
        with self._lock:
            self.response_times.append(duration)
            self.prediction_count += 1
    
    def get_metrics(self) -> Dict[str, float]:
        with self._lock:
            avg_time = np.mean(self.response_times) * 1000 if self.response_times else 0.0
            predictions_per_sec = len(self.response_times) / 60 if self.response_times else 0.0
            
            return {
                "predictions_total": self.prediction_count,
                "predictions_per_second": round(predictions_per_sec, 2),
                "avg_response_time_ms": round(avg_time, 2),
                "min_response_time_ms": round(min(self.response_times) * 1000, 2) if self.response_times else 0.0,
                "max_response_time_ms": round(max(self.response_times) * 1000, 2) if self.response_times else 0.0,
            }

# ==================== FEATURE ENGINEER ====================
class FeatureEngineer:
    def __init__(self):
        self.feature_names = []
        
    def transform(self, window: List[Dict[str, float]]) -> np.ndarray:
        """
        Extract features using the Enterprise pipeline (25 features).
        MUST MATCH train_model.py EnterpriseFeatureEngineer logic exactly.
        """
        if not window or len(window) < 5:
            return np.zeros(25)
            
        sensor_data = defaultdict(list)
        for point in window:
            for sensor, value in point.items():
                if sensor != 'timestamp' and sensor != '_timestamp':
                    sensor_data[sensor].append(float(value))
        
        # Determine primary sensor (pressure preferred, else first available)
        primary_sensor = 'pressure' if 'pressure' in sensor_data else next(iter(sensor_data.keys()), 'pressure')
        values = np.array(sensor_data.get(primary_sensor, []), dtype=np.float32)
        
        if len(values) < 5:
            return np.zeros(25)
            
        features = []
        current_value = values[-1]
        
        # Core statistical features
        features.extend([
            float(np.mean(values)), 
            float(np.std(values)), 
            float(np.min(values)), 
            float(np.max(values)),
            float(np.median(values)), 
            0.0, 0.0,  # Simplified skew/kurtosis to match training
            float(np.percentile(values, 75) - np.percentile(values, 25))
        ])
        
        # Trend analysis
        if len(values) >= 10:
            x = np.arange(len(values))
            try:
                slope, intercept = np.polyfit(x, values, 1)
                features.extend([float(slope), float(intercept)])
            except:
                features.extend([0.0, 0.0])
                
            short_ma = np.mean(values[-5:])
            long_ma = np.mean(values[-10:])
            features.extend([float(short_ma - long_ma), float(short_ma/long_ma if long_ma != 0 else 1)])
            
            # Returns calculation
            if len(values) > 1:
                returns = np.diff(values) / (values[:-1] + 1e-8)
                features.append(float(np.std(returns)) if len(returns) > 0 else 0.0)
            else:
                features.append(0.0)
        else:
            features.extend([0.0, 0.0, 0.0, 1.0, 0.0])
            
        # Pattern detection
        z_score = (current_value - np.mean(values)) / (np.std(values) + 1e-8)
        features.append(float(min(abs(z_score), 10)))
        
        if len(values) >= 2:
            roc = (values[-1] - values[-2]) / (values[-2] + 1e-8)
            features.append(float(min(abs(roc), 5)))
        else:
            features.append(0.0)
            
        # Optimal deviation (using hardcoded range from training logic for consistency)
        optimal_low, optimal_high = 100.0, 150.0
        if current_value < optimal_low:
            features.append(float((optimal_low - current_value) / optimal_low))
        elif current_value > optimal_high:
            features.append(float((current_value - optimal_high) / optimal_high))
        else:
            features.append(0.0)
            
        if len(values) >= 10:
            try:
                lag1_corr = np.corrcoef(values[:-1], values[1:])[0,1] if len(values) > 1 else 0
                features.extend([
                    float(lag1_corr) if not np.isnan(lag1_corr) else 0.0, 
                    float(1 - abs(lag1_corr)) if not np.isnan(lag1_corr) else 1.0
                ])
            except:
                features.extend([0.0, 1.0])
        else:
            features.extend([0.0, 1.0])
            
        # Pad features to exactly 25 dimensions
        while len(features) < 25:
            features.append(0.0)
            
        # Ensure no NaNs or Infs
        return np.nan_to_num(np.array(features[:25], dtype=np.float32), nan=0.0, posinf=10.0, neginf=-10.0)

# ==================== MODEL ARTIFACTS ====================
@dataclass
class ModelArtifacts:
    model: Optional[object] = None
    scaler: Optional[object] = None
    metadata: Dict[str, str] | None = None

@dataclass
class SignalState:
    smoothed_score: float = 0.0
    status: str = "normal"
    last_status_change: float = 0.0

# ==================== PREDICTION ENGINE ====================
class PredictionEngine:
    def __init__(self):
        self.buffers: Dict[str, Deque[Dict[str, float]]] = defaultdict(lambda: deque(maxlen=WINDOW_SIZE))
        self._signal_state: Dict[str, SignalState] = {}
        self.engineer = FeatureEngineer()
        self.artifacts = self._load_artifacts()
        self._lock = threading.RLock()  # Thread safety
        self.performance = PerformanceTracker()
        self._last_cleanup = time.time()

    @staticmethod
    def _load_artifacts() -> ModelArtifacts:
        if not MODEL_DIR.exists():
            print("⚠️ Model directory not found, using rule-based fallback")
            return ModelArtifacts(metadata={"model_version": "rule-based"})

        try:
            model_files = list(MODEL_DIR.glob("*isolation_forest*.pkl")) + list(MODEL_DIR.glob("*model*.pkl"))
            scaler_files = list(MODEL_DIR.glob("*scaler*.pkl"))
            
            if not model_files or not scaler_files:
                print("⚠️ Model files not found, using rule-based fallback")
                return ModelArtifacts(metadata={"model_version": "rule-based"})
            
            # Validate file sizes (basic security check)
            model_file = model_files[0]
            scaler_file = scaler_files[0]
            
            if model_file.stat().st_size < 1000:  # Model should be at least 1KB
                print(f"⚠️ Model file too small ({model_file.stat().st_size} bytes), using rule-based fallback")
                return ModelArtifacts(metadata={"model_version": "rule-based"})
            
            # Load models with version compatibility check
            try:
                import sklearn
                sklearn_version = sklearn.__version__
                print(f"Loading models with scikit-learn {sklearn_version}")
                
                model = joblib.load(model_file)
                scaler = joblib.load(scaler_file)
                
                # Verify model type
                if not hasattr(model, 'decision_function'):
                    print("⚠️ Loaded model doesn't have decision_function, using rule-based fallback")
                    return ModelArtifacts(metadata={"model_version": "rule-based"})
                
                metadata_path = MODEL_DIR / "metadata.json"
                metadata: Dict[str, str] = {}
                if metadata_path.exists():
                    import json
                    metadata = json.loads(metadata_path.read_text())
                    metadata["loaded_sklearn_version"] = sklearn_version
                
                print(f"✅ Models loaded successfully (scikit-learn {sklearn_version})")
                return ModelArtifacts(model=model, scaler=scaler, metadata=metadata)
            except ImportError as e:
                print(f"❌ scikit-learn import error: {e}")
                return ModelArtifacts(metadata={"model_version": "rule-based"})
            except Exception as e:
                print(f"❌ Model loading error: {e}")
                import traceback
                print(traceback.format_exc())
                return ModelArtifacts(metadata={"model_version": "rule-based"})
        except Exception as e:
            print(f"❌ Artifact loading failed: {e}")
            import traceback
            print(traceback.format_exc())
        
        return ModelArtifacts(metadata={"model_version": "rule-based"})

    def _cleanup_old_buffers(self):
        """Remove buffers that haven't been used recently to prevent memory leaks"""
        current_time = time.time()
        if current_time - self._last_cleanup < 300:  # Cleanup every 5 minutes
            return
            
        with self._lock:
            expired_sensors = [
                sensor_id for sensor_id, buffer in self.buffers.items()
                if not buffer or (current_time - self._get_last_timestamp(buffer)) > BUFFER_CLEANUP_MINUTES * 60
            ]
            for sensor_id in expired_sensors:
                del self.buffers[sensor_id]
            
            self._last_cleanup = current_time

    def _get_last_timestamp(self, buffer: Deque) -> float:
        """Extract timestamp from buffer entries"""
        if not buffer:
            return 0.0
        last_entry = buffer[-1]
        # Assuming timestamp is in the data; fallback to current time
        return last_entry.get('_timestamp', time.time())

    def _rule_score(self, readings: Dict[str, float]) -> float:
        score = 0.0
        confidence = 0.8  # Base confidence for rule-based
        
        for name, value in readings.items():
            config = DEFAULT_THRESHOLDS.get(name)
            if not config:
                continue
                
            if value >= config["alarm"]:
                score = max(score, 0.95)
            elif value >= config["warn"]:
                score = max(score, 0.7)
                
        return score

    def _model_score(self, window: List[Dict[str, float]]) -> Optional[float]:
        if not self.artifacts.model or not self.artifacts.scaler:
            return None
            
        try:
            features = self.engineer.transform(window)
            scaled = self.artifacts.scaler.transform([features])
            raw_score = self.artifacts.model.decision_function(scaled)[0]
            return float(1 - ((raw_score + 1) / 2))
        except Exception as e:
            print(f"Model prediction failed: {e}")
            return None

    def _calculate_confidence(self, model_score: Optional[float], rule_score: float, window_size: int) -> float:
        """Calculate prediction confidence based on multiple factors"""
        confidence = 0.8  # Base confidence
        
        # Increase confidence if both methods agree
        if model_score and abs(model_score - rule_score) < 0.2:
            confidence += 0.1
            
        # Increase confidence with more data
        if window_size >= 30:
            confidence += 0.05
        elif window_size >= 50:
            confidence += 0.1
            
        return min(confidence, 0.95)

    def predict(self, payload: PredictPayload) -> PredictResponse:
        start_time = time.perf_counter()
        
        # Periodic cleanup
        self._cleanup_old_buffers()
        
        with self.performance.track_prediction():
            with self._lock:  # Thread-safe buffer access
                # Add timestamp for cleanup
                payload_data = payload.readings.copy()
                payload_data['_timestamp'] = time.time()
                
                buffer = self.buffers[payload.sensor_id]
                buffer.append(payload_data)

                if len(buffer) < MIN_SAMPLES:
                    return PredictResponse(
                        prediction="normal",
                        status="buffering",
                        score=0.0,
                        confidence=0.7,
                        anomaly_type="BASELINE",
                        model_version=self.artifacts.metadata.get("model_version", "rule-based") if self.artifacts.metadata else "rule-based",
                        rul=100.0,
                        response_time_ms=round((time.perf_counter() - start_time) * 1000, 2),
                        contributing_features={"buffer_size": len(buffer)}
                    )

                window = list(buffer)
                model_score = self._model_score(window)
                rule_score = self._rule_score(payload.readings)
                raw_score = max(model_score or 0.0, rule_score)

                # Smooth the score (EMA) and apply hysteresis + dwell-time.
                now_ts = time.time()
                state = self._signal_state.get(payload.sensor_id)
                if state is None:
                    state = SignalState(smoothed_score=raw_score, status="normal", last_status_change=now_ts)
                    self._signal_state[payload.sensor_id] = state
                else:
                    state.smoothed_score = (EMA_ALPHA * raw_score) + ((1 - EMA_ALPHA) * state.smoothed_score)

                score = float(max(0.0, min(1.0, state.smoothed_score)))
                confidence = self._calculate_confidence(model_score, rule_score, len(window))

                # Status transitions with hysteresis.
                prev_status = state.status

                if prev_status == "critical":
                    if score < HYSTERESIS["critical_exit"] and (now_ts - state.last_status_change) >= MIN_STATUS_DWELL_SECONDS:
                        state.status = "warning" if score >= HYSTERESIS["warning_enter"] else "normal"
                elif prev_status == "warning":
                    if score >= HYSTERESIS["critical_enter"]:
                        state.status = "critical"
                    elif score < HYSTERESIS["warning_exit"] and (now_ts - state.last_status_change) >= MIN_STATUS_DWELL_SECONDS:
                        state.status = "normal"
                else:  # normal
                    if score >= HYSTERESIS["critical_enter"]:
                        state.status = "critical"
                    elif score >= HYSTERESIS["warning_enter"]:
                        state.status = "warning"

                if state.status != prev_status:
                    state.last_status_change = now_ts

                status = state.status
                if status == "critical":
                    anomaly_type = "CRITICAL"
                elif status == "warning":
                    anomaly_type = "WARNING"
                else:
                    anomaly_type = "NORMAL"

                response_time_ms = (time.perf_counter() - start_time) * 1000

                return PredictResponse(
                    prediction="anomaly" if status != "normal" else "normal",
                    status=status,
                    score=round(score, 4),
                    confidence=round(confidence, 3),
                    anomaly_type=anomaly_type,
                    model_version=self.artifacts.metadata.get("model_version", "rule-based") if self.artifacts.metadata else "rule-based",
                    # Make RUL less jumpy and more industrial: non-linear, based on smoothed score.
                    rul=max(0.0, min(100.0, ((1 - score) ** 2) * 100)),
                    response_time_ms=round(response_time_ms, 2),
                    contributing_features={
                        "rule_score": round(rule_score, 4),
                        "model_score": round(model_score, 4) if model_score else 0.0,
                        "window_size": len(window),
                        "buffer_utilization": round(len(window) / WINDOW_SIZE, 2),
                        "raw_score": round(raw_score, 4),
                        "smoothed_score": round(score, 4),
                        "state_status": status,
                    },
                )

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance and resource metrics"""
        import psutil
        process = psutil.Process()
        
        return {
            "memory_usage_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "cpu_percent": process.cpu_percent(),
            "active_buffers": len(self.buffers),
            "total_buffer_entries": sum(len(buf) for buf in self.buffers.values()),
            "model_status": "loaded" if self.artifacts.model else "rule_based"
        }

# ==================== FASTAPI APP ====================
engine = PredictionEngine()
app = FastAPI(
    title="AI Anomaly Detection Service",
    description="Production-ready AI-powered anomaly detection for industrial sensors",
    version=engine.artifacts.metadata.get("model_version", "1.0.0") if engine.artifacts.metadata else "1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ==================== API ENDPOINTS ====================
@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        model_loaded=engine.artifacts.model is not None,
        model_version=engine.artifacts.metadata.get("model_version", "rule-based") if engine.artifacts.metadata else "rule-based",
        buffers=len(engine.buffers),
        performance=engine.performance.get_metrics(),
        system_metrics=engine.get_system_metrics()
    )

@app.get("/metrics", response_model=MetricsResponse)
async def metrics():
    perf_metrics = engine.performance.get_metrics()
    system_metrics = engine.get_system_metrics()
    
    return MetricsResponse(
        predictions_total=perf_metrics["predictions_total"],
        predictions_per_second=perf_metrics["predictions_per_second"],
        avg_response_time_ms=perf_metrics["avg_response_time_ms"],
        active_buffers=system_metrics["active_buffers"],
        memory_usage_mb=system_metrics["memory_usage_mb"]
    )

@app.get("/system/status")
async def system_status():
    """Comprehensive system status"""
    return {
        "service": "AI Anomaly Detection",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "model": {
            "loaded": engine.artifacts.model is not None,
            "version": engine.artifacts.metadata.get("model_version", "rule-based") if engine.artifacts.metadata else "rule-based",
            "type": "Isolation Forest + Rule Engine"
        },
        "buffers": {
            "active": len(engine.buffers),
            "total_entries": sum(len(buf) for buf in engine.buffers.values()),
            "window_size": WINDOW_SIZE,
            "min_samples": MIN_SAMPLES
        },
        "performance": engine.performance.get_metrics(),
        "system": engine.get_system_metrics()
    }

@app.post("/predict", response_model=PredictResponse)
async def predict(payload: PredictPayload):
    if not payload.readings:
        raise HTTPException(status_code=400, detail="Readings cannot be empty")
    
    if not any(isinstance(v, (int, float)) for v in payload.readings.values()):
        raise HTTPException(status_code=400, detail="Readings must contain numeric values")
    
    return engine.predict(payload)

@app.post("/admin/buffers/cleanup")
async def cleanup_buffers():
    """Manual trigger for buffer cleanup"""
    engine._cleanup_old_buffers()
    return {"status": "cleanup_completed", "active_buffers": len(engine.buffers)}

@app.get("/admin/buffers/status")
async def buffer_status():
    """Get detailed buffer status"""
    buffer_info = {}
    for sensor_id, buffer in engine.buffers.items():
        buffer_info[sensor_id] = {
            "size": len(buffer),
            "latest_timestamp": engine._get_last_timestamp(buffer),
            "ready": len(buffer) >= MIN_SAMPLES
        }
    
    return buffer_info

# ==================== MAIN ====================
if __name__ == "__main__":
    import uvicorn
    
    print("Starting AI Anomaly Detection Service...")
    print("Health: http://localhost:8000/health")
    print("Metrics: http://localhost:8000/metrics")
    print("System Status: http://localhost:8000/system/status")
    print("Predictions: POST http://localhost:8000/predict")
    print("API Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
        access_log=True
    )