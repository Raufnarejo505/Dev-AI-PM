"""
Database models for machine state tracking and configuration
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class MachineStateEnum(str, Enum):
    """Machine operating states"""
    OFF = "OFF"
    HEATING = "HEATING"
    IDLE = "IDLE"
    PRODUCTION = "PRODUCTION"
    COOLING = "COOLING"
    UNKNOWN = "UNKNOWN"
    SENSOR_FAULT = "SENSOR_FAULT"


class MachineState(Base):
    """Machine state history table"""
    __tablename__ = "machine_state"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_id = Column(String(100), nullable=False, index=True)
    machine_uuid = Column(UUID(as_uuid=True), ForeignKey('machine.id'), nullable=True)
    
    # State information
    state = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0 - 1.0
    state_since = Column(DateTime(timezone=True), nullable=False)
    last_updated = Column(DateTime(timezone=True), nullable=False)
    
    # Derived metrics
    temp_avg = Column(Float)
    temp_spread = Column(Float)
    d_temp_avg = Column(Float)  # °C/min
    rpm_stable = Column(Float)
    pressure_stable = Column(Float)
    
    # Flags
    any_temp_above_min = Column(Boolean, default=False)
    all_temps_below = Column(Boolean, default=True)
    
    # Additional metadata
    flags = Column(JSON)  # Additional state flags
    state_metadata = Column(JSON)  # Additional metadata
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    machine = relationship("Machine", foreign_keys=[machine_uuid], back_populates="states")
    
    def __repr__(self):
        return f"<MachineState {self.machine_id}: {self.state} ({self.confidence:.2f})>"


class MachineStateThresholds(Base):
    """Per-machine state detection thresholds configuration"""
    __tablename__ = "machine_state_thresholds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_id = Column(String(100), nullable=False, unique=True, index=True)
    machine_uuid = Column(UUID(as_uuid=True), ForeignKey('machine.id'), nullable=True)
    
    # Core thresholds
    rpm_on = Column(Float, default=5.0)          # rpm - movement present
    rpm_prod = Column(Float, default=10.0)       # rpm - production possible
    p_on = Column(Float, default=2.0)            # bar - pressure present
    p_prod = Column(Float, default=5.0)          # bar - typical production pressure
    t_min_active = Column(Float, default=60.0)   # °C - below this = cold/off
    
    # Temperature rate thresholds
    heating_rate = Column(Float, default=0.2)    # °C/min - positive heating
    cooling_rate = Column(Float, default=-0.2)   # °C/min - negative cooling
    
    # Stability thresholds
    temp_flat_rate = Column(Float, default=0.2)  # °C/min - considered flat
    rpm_stable_max = Column(Float, default=2.0)  # rpm std dev for stable
    pressure_stable_max = Column(Float, default=1.0)  # bar std dev for stable
    
    # Hysteresis timers (seconds)
    production_enter_time = Column(Integer, default=90)    # seconds
    production_exit_time = Column(Integer, default=120)    # seconds
    state_change_debounce = Column(Integer, default=60)    # seconds
    
    # Optional thresholds
    motor_load_min = Column(Float, default=0.15)   # 15% for production fallback
    throughput_min = Column(Float, default=0.1)    # kg/h for production fallback
    
    # Metadata
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))  # User who created this config
    
    # Relationships
    machine = relationship("Machine", foreign_keys=[machine_uuid], back_populates="state_thresholds")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "machine_id": self.machine_id,
            "rpm_on": self.rpm_on,
            "rpm_prod": self.rpm_prod,
            "p_on": self.p_on,
            "p_prod": self.p_prod,
            "t_min_active": self.t_min_active,
            "heating_rate": self.heating_rate,
            "cooling_rate": self.cooling_rate,
            "temp_flat_rate": self.temp_flat_rate,
            "rpm_stable_max": self.rpm_stable_max,
            "pressure_stable_max": self.pressure_stable_max,
            "production_enter_time": self.production_enter_time,
            "production_exit_time": self.production_exit_time,
            "state_change_debounce": self.state_change_debounce,
            "motor_load_min": self.motor_load_min,
            "throughput_min": self.throughput_min,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by
        }


class MachineStateTransition(Base):
    """Log of machine state transitions for audit and analysis"""
    __tablename__ = "machine_state_transition"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_id = Column(String(100), nullable=False, index=True)
    machine_uuid = Column(UUID(as_uuid=True), ForeignKey('machine.id'), nullable=True)
    
    # Transition information
    from_state = Column(String(20))
    to_state = Column(String(20), nullable=False)
    transition_reason = Column(String(200))  # Brief reason for transition
    
    # Timing information
    transition_time = Column(DateTime(timezone=True), nullable=False)
    previous_state_duration = Column(Float)  # Duration in seconds
    
    # State information at transition
    confidence_before = Column(Float)
    confidence_after = Column(Float)
    
    # Sensor readings at transition
    sensor_data = Column(JSON)  # Snapshot of sensor readings at transition
    
    # Metadata
    transition_metadata = Column(JSON)  # Additional transition metadata
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MachineStateTransition {self.machine_id}: {self.from_state} → {self.to_state}>"


class MachineStateAlert(Base):
    """Alerts generated from machine state changes"""
    __tablename__ = "machine_state_alert"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_id = Column(String(100), nullable=False, index=True)
    machine_uuid = Column(UUID(as_uuid=True), ForeignKey('machine.id'), nullable=True)
    
    # Alert information
    alert_type = Column(String(50), nullable=False)  # e.g., "STATE_CHANGE", "SENSOR_FAULT"
    severity = Column(String(20), nullable=False)    # info, warning, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # State information
    state = Column(String(20))  # State that triggered the alert
    previous_state = Column(String(20))  # Previous state if applicable
    
    # Timing
    alert_time = Column(DateTime(timezone=True), nullable=False)
    
    # Status
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime(timezone=True))
    
    # Resolution
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    
    # Metadata
    alert_metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    machine = relationship("Machine", foreign_keys=[machine_uuid], back_populates="state_alerts")
    
    def __repr__(self):
        return f"<MachineStateAlert {self.machine_id}: {self.alert_type} - {self.title}>"


class MachineProcessEvaluation(Base):
    """Process evaluation results (only stored for PRODUCTION state)"""
    __tablename__ = "machine_process_evaluation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_id = Column(String(100), nullable=False, index=True)
    machine_uuid = Column(UUID(as_uuid=True), ForeignKey('machine.id'), nullable=True)
    
    # Evaluation timestamp
    evaluation_time = Column(DateTime(timezone=True), nullable=False)
    
    # Traffic light status
    traffic_light_status = Column(String(20))  # GREEN, YELLOW, RED
    traffic_light_score = Column(Float)        # 0.0 - 1.0
    traffic_light_reason = Column(Text)        # Reason for status
    
    # Baseline comparison
    baseline_deviation = Column(Float)         # Deviation from baseline (%)
    baseline_status = Column(String(20))       # NORMAL, DEVIATING, CRITICAL
    
    # Anomaly detection
    anomaly_detected = Column(Boolean, default=False)
    anomaly_score = Column(Float)              # 0.0 - 1.0
    anomaly_features = Column(JSON)           # Contributing features
    
    # Process metrics
    process_efficiency = Column(Float)        # Process efficiency %
    quality_score = Column(Float)             # Quality score 0.0 - 1.0
    
    # Recommendations
    recommendations = Column(JSON)             # List of recommendations
    
    # Metadata
    evaluation_model_version = Column(String(50))  # AI model version
    evaluation_metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MachineProcessEvaluation {self.machine_id}: {self.traffic_light_status} at {self.evaluation_time}>"
