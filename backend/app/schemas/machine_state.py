"""
Pydantic schemas for machine state API
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field, validator


class MachineStateEnum(str, Enum):
    """Machine operating states"""
    OFF = "OFF"
    HEATING = "HEATING"
    IDLE = "IDLE"
    PRODUCTION = "PRODUCTION"
    COOLING = "COOLING"
    UNKNOWN = "UNKNOWN"
    SENSOR_FAULT = "SENSOR_FAULT"


class DerivedMetrics(BaseModel):
    """Derived metrics from sensor readings"""
    temp_avg: Optional[float] = None
    temp_spread: Optional[float] = None
    d_temp_avg: Optional[float] = None  # °C/min
    rpm_stable: Optional[float] = None
    pressure_stable: Optional[float] = None
    any_temp_above_min: bool = False
    all_temps_below: bool = True


class MachineStateInfo(BaseModel):
    """Current machine state information"""
    machine_id: str
    state: MachineStateEnum
    confidence: float = Field(..., ge=0.0, le=1.0, description="State confidence 0.0-1.0")
    state_since: datetime
    last_updated: datetime
    metrics: DerivedMetrics
    flags: Optional[Dict[str, Any]] = None
    state_duration_seconds: Optional[float] = None

    class Config:
        from_attributes = True


class MachineStateThresholds(BaseModel):
    """Machine state detection thresholds"""
    rpm_on: float = Field(default=5.0, description="RPM threshold for movement detection")
    rpm_prod: float = Field(default=10.0, description="RPM threshold for production")
    p_on: float = Field(default=2.0, description="Pressure threshold for presence detection")
    p_prod: float = Field(default=5.0, description="Pressure threshold for production")
    t_min_active: float = Field(default=60.0, description="Minimum temperature for active state")
    
    heating_rate: float = Field(default=0.2, description="Heating rate threshold (°C/min)")
    cooling_rate: float = Field(default=-0.2, description="Cooling rate threshold (°C/min)")
    
    temp_flat_rate: float = Field(default=0.2, description="Temperature rate considered flat (°C/min)")
    rpm_stable_max: float = Field(default=2.0, description="Max RPM std dev for stable state")
    pressure_stable_max: float = Field(default=1.0, description="Max pressure std dev for stable state")
    
    production_enter_time: int = Field(default=90, description="Time required to enter production (seconds)")
    production_exit_time: int = Field(default=120, description="Time required to exit production (seconds)")
    state_change_debounce: int = Field(default=60, description="Debounce time for state changes (seconds)")
    
    motor_load_min: float = Field(default=0.15, description="Minimum motor load for production fallback")
    throughput_min: float = Field(default=0.1, description="Minimum throughput for production fallback")
    
    description: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class MachineStateThresholdsCreate(MachineStateThresholds):
    """Schema for creating machine state thresholds"""
    machine_id: str = Field(..., description="Machine ID")


class MachineStateThresholdsUpdate(BaseModel):
    """Schema for updating machine state thresholds"""
    rpm_on: Optional[float] = None
    rpm_prod: Optional[float] = None
    p_on: Optional[float] = None
    p_prod: Optional[float] = None
    t_min_active: Optional[float] = None
    
    heating_rate: Optional[float] = None
    cooling_rate: Optional[float] = None
    
    temp_flat_rate: Optional[float] = None
    rpm_stable_max: Optional[float] = None
    pressure_stable_max: Optional[float] = None
    
    production_enter_time: Optional[int] = None
    production_exit_time: Optional[int] = None
    state_change_debounce: Optional[int] = None
    
    motor_load_min: Optional[float] = None
    throughput_min: Optional[float] = None
    
    description: Optional[str] = None
    is_active: Optional[bool] = None


class MachineStateTransition(BaseModel):
    """Machine state transition information"""
    id: str
    machine_id: str
    from_state: Optional[MachineStateEnum]
    to_state: MachineStateEnum
    transition_reason: Optional[str]
    transition_time: datetime
    previous_state_duration: Optional[float]
    confidence_before: Optional[float]
    confidence_after: Optional[float]
    sensor_data: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class MachineStateAlert(BaseModel):
    """Machine state alert information"""
    id: str
    machine_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    state: Optional[MachineStateEnum]
    previous_state: Optional[MachineStateEnum]
    alert_time: datetime
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    is_resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class MachineProcessEvaluation(BaseModel):
    """Process evaluation results (PRODUCTION state only)"""
    id: str
    machine_id: str
    evaluation_time: datetime
    traffic_light_status: Optional[str]  # GREEN, YELLOW, RED
    traffic_light_score: Optional[float]
    traffic_light_reason: Optional[str]
    baseline_deviation: Optional[float]
    baseline_status: Optional[str]
    anomaly_detected: bool = False
    anomaly_score: Optional[float]
    anomaly_features: Optional[Dict[str, Any]]
    process_efficiency: Optional[float]
    quality_score: Optional[float]
    recommendations: Optional[List[str]]
    evaluation_model_version: Optional[str]
    metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class SensorReading(BaseModel):
    """Sensor reading for state detection"""
    timestamp: datetime
    screw_rpm: Optional[float] = None
    pressure_bar: Optional[float] = None
    temp_zone_1: Optional[float] = None
    temp_zone_2: Optional[float] = None
    temp_zone_3: Optional[float] = None
    temp_zone_4: Optional[float] = None
    motor_load: Optional[float] = None
    throughput_kg_h: Optional[float] = None
    line_enable: Optional[bool] = None
    heater_on: Optional[bool] = None
    heater_power: Optional[float] = None

    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v > datetime.utcnow():
            raise ValueError("Timestamp cannot be in the future")
        return v


class MachineStateHistory(BaseModel):
    """Machine state history for a time period"""
    machine_id: str
    start_time: datetime
    end_time: datetime
    states: List[MachineStateTransition]
    current_state: Optional[MachineStateInfo] = None


class MachineStateStatistics(BaseModel):
    """Statistics for machine states over time period"""
    machine_id: str
    start_time: datetime
    end_time: datetime
    
    # Time spent in each state (percentage)
    off_percentage: float
    heating_percentage: float
    idle_percentage: float
    production_percentage: float
    cooling_percentage: float
    unknown_percentage: float
    
    # Time spent in each state (hours)
    off_hours: float
    heating_hours: float
    idle_hours: float
    production_hours: float
    cooling_hours: float
    unknown_hours: float
    
    # Transition counts
    total_transitions: int
    state_changes: List[Dict[str, Any]]
    
    # Production metrics (if applicable)
    production_cycles: Optional[int] = None
    avg_production_duration: Optional[float] = None
    total_production_time: Optional[float] = None


class MachineStateConfigRequest(BaseModel):
    """Request to configure machine state detection"""
    machine_id: str
    thresholds: MachineStateThresholds
    enable_process_evaluation: bool = True
    alert_on_state_change: bool = True
    alert_on_sensor_fault: bool = True


class MachineStateConfigResponse(BaseModel):
    """Response for machine state configuration"""
    machine_id: str
    configured: bool
    thresholds: MachineStateThresholds
    message: str


class MachineStateBulkRequest(BaseModel):
    """Bulk request for multiple machines"""
    machine_ids: List[str] = Field(..., description="List of machine IDs")


class MachineStateBulkResponse(BaseModel):
    """Bulk response for multiple machines"""
    states: Dict[str, MachineStateInfo]
    errors: Dict[str, str] = {}
    timestamp: datetime


class TrafficLightStatus(BaseModel):
    """Traffic light status for production state"""
    machine_id: str
    status: str  # GREEN, YELLOW, RED
    score: float = Field(..., ge=0.0, le=1.0)
    reason: str
    evaluation_time: datetime
    recommendations: List[str] = []


class ProcessEvaluationRequest(BaseModel):
    """Request to trigger process evaluation"""
    machine_id: str
    force_evaluation: bool = False  # Force evaluation even if not in production


class ProcessEvaluationResponse(BaseModel):
    """Response for process evaluation"""
    machine_id: str
    evaluation_performed: bool
    traffic_light: Optional[TrafficLightStatus] = None
    message: str
    evaluation_time: datetime
