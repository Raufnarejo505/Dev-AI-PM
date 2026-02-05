"""
Feature Engineering Service
Converts raw sensor readings to feature vectors for ML models
"""
from typing import Dict, List, Any
import numpy as np
from loguru import logger


class FeatureService:
    """Service for feature engineering from sensor data"""
    
    @staticmethod
    def normalize_value(value: Any, min_val: float = None, max_val: float = None) -> float:
        """Normalize a value to 0-1 range"""
        try:
            val = float(value)
            if min_val is not None and max_val is not None:
                if max_val == min_val:
                    return 0.5
                return (val - min_val) / (max_val - min_val)
            return val
        except (ValueError, TypeError):
            logger.warning(f"Failed to normalize value: {value}")
            return 0.0
    
    @staticmethod
    def extract_features(readings: Dict[str, float]) -> List[float]:
        """
        Extract feature vector from sensor readings
        Returns: [vibration, temperature, rpm, vibration*temp_ratio, rolling_mean, etc.]
        """
        features = []
        
        # Extract primary sensor values
        vibration = float(readings.get("vibration", readings.get("vib", 0.0)))
        temperature = float(readings.get("temperature", readings.get("temp", 0.0)))
        rpm = float(readings.get("rpm", readings.get("speed", 0.0)))
        pressure = float(readings.get("pressure", readings.get("press", 0.0)))
        flow_rate = float(readings.get("flow_rate", readings.get("flow", 0.0)))
        motor_current = float(readings.get("motor_current", readings.get("current", 0.0)))
        
        # Primary features
        features.extend([vibration, temperature, rpm])
        
        # Derived features
        if temperature > 0:
            temp_ratio = vibration / temperature if temperature > 0 else 0.0
            features.append(temp_ratio)
        else:
            features.append(0.0)
        
        # Rolling statistics (simplified - using current values)
        # In production, this would use a window of historical values
        mean_value = np.mean([v for v in [vibration, temperature, rpm, pressure, flow_rate, motor_current] if v > 0])
        features.append(mean_value)
        
        # Additional derived features
        features.append(abs(vibration - temperature) if temperature > 0 else 0.0)  # Difference
        features.append(vibration * rpm / 1000.0 if rpm > 0 else 0.0)  # Interaction
        features.append(pressure if pressure > 0 else 0.0)
        features.append(flow_rate if flow_rate > 0 else 0.0)
        features.append(motor_current if motor_current > 0 else 0.0)
        
        # Ensure all values are finite
        features = [float(np.nan_to_num(f, nan=0.0, posinf=10.0, neginf=-10.0)) for f in features]
        
        return features
    
    @staticmethod
    def validate_readings(readings: Dict[str, Any]) -> Dict[str, float]:
        """
        Validate and convert readings to float
        Returns validated dictionary with float values
        """
        validated = {}
        for key, value in readings.items():
            try:
                validated[key] = float(value)
            except (ValueError, TypeError):
                logger.warning(f"Invalid reading value for {key}: {value}, skipping")
                continue
        return validated
    
    @staticmethod
    def prepare_for_ai(readings: Dict[str, Any]) -> Dict[str, float]:
        """
        Prepare sensor readings for AI service
        Validates, normalizes, and formats readings
        """
        validated = FeatureService.validate_readings(readings)
        
        # Ensure we have at least one valid reading
        if not validated:
            logger.error("No valid readings found after validation")
            return {"value": 0.0}
        
        return validated

