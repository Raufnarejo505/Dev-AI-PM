from typing import List, Dict, Any
import numpy as np

class RingBuffer:
    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self.buffer = []
        self.is_full = False
        
    def add_data(self, data_point: Dict[str, Any]):
        """Add new data point to buffer"""
        self.buffer.append(data_point)
        
        # Maintain fixed window size
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)
            self.is_full = True
            
    def get_window(self) -> List[Dict[str, Any]]:
        """Get current window data"""
        return self.buffer.copy()
    
    def is_ready(self) -> bool:
        """Check if buffer has enough data"""
        return len(self.buffer) >= self.window_size
    
    def current_size(self) -> int:
        """Get current buffer size"""
        return len(self.buffer)
    
    def clear(self):
        """Clear the buffer"""
        self.buffer = []
        self.is_full = False