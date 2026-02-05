import numpy as np
import pandas as pd
from typing import List, Dict, Any

class FeatureExtractor:
    def __init__(self):
        self.feature_names = []
        
    def extract_features(self, window_data: List[Dict[str, Any]]) -> np.ndarray:
        """Extract statistical features from sensor window"""
        if not window_data:
            return np.array([])
            
        df = pd.DataFrame(window_data)
        features = []
        feature_names = []
        
        sensor_columns = ['pressure', 'temperature', 'flow_rate', 'motor_current', 'vibration']
        
        for col in sensor_columns:
            if col in df.columns:
                values = df[col].values
                
                # Statistical features
                features.extend([
                    np.mean(values),    # mean
                    np.std(values),     # standard deviation
                    np.min(values),     # minimum
                    np.max(values),     # maximum
                    np.median(values),  # median
                ])
                feature_names.extend([
                    f"{col}_mean", f"{col}_std", f"{col}_min", 
                    f"{col}_max", f"{col}_median"
                ])
                
                # Additional features
                features.extend([
                    np.percentile(values, 25),  # Q1
                    np.percentile(values, 75),  # Q3
                    values[-1] - values[0],     # trend
                ])
                feature_names.extend([
                    f"{col}_q1", f"{col}_q3", f"{col}_trend"
                ])
        
        self.feature_names = feature_names
        return np.array(features)
    
    def get_feature_names(self) -> List[str]:
        return self.feature_names