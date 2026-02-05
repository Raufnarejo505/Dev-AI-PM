class HysteresisManager:
    def __init__(self):
        self.warn_threshold = 0.7
        self.alarm_threshold = 0.9
        self.hysteresis_margin = 0.1
        self.current_status = "OK"
        self.consecutive_count = 0
        self.required_consecutive = 3
        
    def get_status(self, anomaly_score: float) -> str:
        """Apply hysteresis to determine status"""
        
        if anomaly_score >= self.alarm_threshold:
            if self.current_status != "ALARM":
                self.consecutive_count += 1
                if self.consecutive_count >= self.required_consecutive:
                    self.current_status = "ALARM"
                    self.consecutive_count = 0
            else:
                self.consecutive_count = 0
                
        elif anomaly_score >= self.warn_threshold:
            if self.current_status == "OK":
                self.consecutive_count += 1
                if self.consecutive_count >= self.required_consecutive:
                    self.current_status = "WARN"
                    self.consecutive_count = 0
            elif self.current_status == "ALARM" and anomaly_score < (self.alarm_threshold - self.hysteresis_margin):
                self.consecutive_count += 1
                if self.consecutive_count >= self.required_consecutive:
                    self.current_status = "WARN"
                    self.consecutive_count = 0
            else:
                self.consecutive_count = 0
                
        else:  # anomaly_score < warn_threshold
            if self.current_status != "OK":
                self.consecutive_count += 1
                if self.consecutive_count >= self.required_consecutive:
                    self.current_status = "OK"
                    self.consecutive_count = 0
            else:
                self.consecutive_count = 0
                
        return self.current_status
    
    def reset(self):
        """Reset hysteresis state"""
        self.current_status = "OK"
        self.consecutive_count = 0