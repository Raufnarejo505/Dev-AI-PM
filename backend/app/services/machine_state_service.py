"""
Machine State Detection Service

Implements intelligent machine state detection with 5 states:
- OFF: Machine off / cold
- HEATING: Warming up, not producing
- IDLE: Warm and ready, but not producing
- PRODUCTION: Active process (traffic light + baseline + anomalies enabled)
- COOLING: Cooling down, not producing
- UNKNOWN: Sensor fault / invalid data

Process evaluation (traffic-light, baseline, anomalies) only runs in PRODUCTION.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import deque
import statistics

logger = logging.getLogger(__name__)

class MachineState(Enum):
    """Machine operating states"""
    OFF = "OFF"
    HEATING = "HEATING"
    IDLE = "IDLE"
    PRODUCTION = "PRODUCTION"
    COOLING = "COOLING"
    UNKNOWN = "UNKNOWN"
    SENSOR_FAULT = "SENSOR_FAULT"

@dataclass
class StateThresholds:
    """Configurable thresholds for state detection"""
    # Core thresholds
    RPM_ON: float = 5.0          # rpm - movement present
    RPM_PROD: float = 10.0       # rpm - production possible
    P_ON: float = 2.0            # bar - pressure present
    P_PROD: float = 5.0          # bar - typical production pressure
    T_MIN_ACTIVE: float = 60.0   # °C - below this = cold/off
    
    # Temperature rate thresholds
    HEATING_RATE: float = 0.2    # °C/min - positive heating
    COOLING_RATE: float = -0.2   # °C/min - negative cooling
    
    # Stability thresholds
    TEMP_FLAT_RATE: float = 0.2  # °C/min - considered flat
    RPM_STABLE_MAX: float = 2.0  # rpm std dev for stable
    PRESSURE_STABLE_MAX: float = 1.0  # bar std dev for stable
    
    # Hysteresis timers (seconds)
    PRODUCTION_ENTER_TIME: int = 90    # seconds
    PRODUCTION_EXIT_TIME: int = 120    # seconds
    STATE_CHANGE_DEBOUNCE: int = 60    # seconds
    
    # Optional thresholds
    MOTOR_LOAD_MIN: float = 0.15   # 15% for production fallback
    THROUGHPUT_MIN: float = 0.1    # kg/h for production fallback

@dataclass
class SensorReading:
    """Single sensor reading with timestamp"""
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

@dataclass
class DerivedMetrics:
    """Derived metrics from sensor readings"""
    temp_avg: Optional[float] = None
    temp_spread: Optional[float] = None
    d_temp_avg: Optional[float] = None  # °C/min
    rpm_stable: Optional[float] = None
    pressure_stable: Optional[float] = None
    any_temp_above_min: bool = False
    all_temps_below: bool = True

@dataclass
class MachineStateInfo:
    """Current machine state with metadata"""
    state: MachineState
    confidence: float  # 0.0 - 1.0
    state_since: datetime
    last_updated: datetime
    metrics: DerivedMetrics
    flags: Dict[str, Any] = None

class StateTimer:
    """Manages hysteresis timers for state transitions"""
    def __init__(self):
        self.timers: Dict[str, datetime] = {}
        self.state_start_times: Dict[MachineState, datetime] = {}
    
    def start_timer(self, timer_name: str, duration_seconds: int) -> datetime:
        """Start a timer and return expiry time"""
        expiry = datetime.utcnow() + timedelta(seconds=duration_seconds)
        self.timers[timer_name] = expiry
        return expiry
    
    def is_timer_expired(self, timer_name: str) -> bool:
        """Check if timer has expired"""
        if timer_name not in self.timers:
            return True
        return datetime.utcnow() >= self.timers[timer_name]
    
    def clear_timer(self, timer_name: str):
        """Clear a timer"""
        self.timers.pop(timer_name, None)
    
    def set_state_start(self, state: MachineState):
        """Record when a state started"""
        self.state_start_times[state] = datetime.utcnow()
    
    def get_state_duration(self, state: MachineState) -> timedelta:
        """Get how long current state has been active"""
        if state not in self.state_start_times:
            return timedelta(0)
        return datetime.utcnow() - self.state_start_times[state]

class MachineStateDetector:
    """Main machine state detection service"""
    
    def __init__(self, machine_id: str, thresholds: Optional[StateThresholds] = None):
        self.machine_id = machine_id
        self.thresholds = thresholds or StateThresholds()
        self.timer = StateTimer()
        
        # Data buffers for calculations (2 minutes of data)
        self.reading_buffer: deque = deque(maxlen=120)  # Assuming 1-second intervals
        self.temp_history: deque = deque(maxlen=300)   # 5 minutes for temperature slope
        
        # Current state
        self.current_state: MachineStateInfo = MachineStateInfo(
            state=MachineState.UNKNOWN,
            confidence=0.0,
            state_since=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            metrics=DerivedMetrics()
        )
        
        logger.info(f"Machine state detector initialized for {machine_id}")
    
    def add_reading(self, reading: SensorReading) -> MachineStateInfo:
        """Add new sensor reading and update state"""
        try:
            # Add to buffers
            self.reading_buffer.append(reading)
            
            # Calculate derived metrics
            metrics = self._calculate_derived_metrics(reading)
            
            # Check for sensor faults
            if self._detect_sensor_fault(reading, metrics):
                new_state = MachineState.SENSOR_FAULT
                confidence = 0.0
            else:
                # Determine new state
                new_state, confidence = self._determine_state(reading, metrics)
            
            # Apply hysteresis/debounce
            final_state, final_confidence = self._apply_hysteresis(new_state, confidence)
            
            # Update current state if changed
            if final_state != self.current_state.state:
                self.current_state.state = final_state
                self.current_state.confidence = final_confidence
                self.current_state.state_since = datetime.utcnow()
                self.timer.set_state_start(final_state)
                
                logger.info(f"Machine {self.machine_id} state changed: {final_state.value}")
            
            self.current_state.last_updated = datetime.utcnow()
            self.current_state.metrics = metrics
            
            return self.current_state
            
        except Exception as e:
            logger.error(f"Error processing reading for {self.machine_id}: {e}")
            # Return fault state on error
            self.current_state.state = MachineState.SENSOR_FAULT
            self.current_state.confidence = 0.0
            self.current_state.last_updated = datetime.utcnow()
            return self.current_state
    
    def _calculate_derived_metrics(self, reading: SensorReading) -> DerivedMetrics:
        """Calculate derived metrics from sensor reading"""
        # Temperature metrics
        temps = [reading.temp_zone_1, reading.temp_zone_2, reading.temp_zone_3, reading.temp_zone_4]
        valid_temps = [t for t in temps if t is not None]
        
        temp_avg = statistics.mean(valid_temps) if valid_temps else None
        temp_spread = max(valid_temps) - min(valid_temps) if len(valid_temps) >= 2 else None
        
        # Temperature slope (°C/min) - need historical data
        d_temp_avg = self._calculate_temperature_slope(temp_avg)
        
        # Stability metrics (std dev over last 60 seconds)
        rpm_stable = self._calculate_stability_metric('screw_rpm')
        pressure_stable = self._calculate_stability_metric('pressure_bar')
        
        # Convenience flags
        any_temp_above_min = any(t > self.thresholds.T_MIN_ACTIVE for t in valid_temps) if valid_temps else False
        all_temps_below = all(t < self.thresholds.T_MIN_ACTIVE for t in valid_temps) if valid_temps else True
        
        return DerivedMetrics(
            temp_avg=temp_avg,
            temp_spread=temp_spread,
            d_temp_avg=d_temp_avg,
            rpm_stable=rpm_stable,
            pressure_stable=pressure_stable,
            any_temp_above_min=any_temp_above_min,
            all_temps_below=all_temps_below
        )
    
    def _calculate_temperature_slope(self, current_temp: Optional[float]) -> Optional[float]:
        """Calculate temperature slope in °C/min"""
        if current_temp is None:
            return None
        
        # Add current temperature to history
        self.temp_history.append((datetime.utcnow(), current_temp))
        
        # Need at least 2 minutes of data for meaningful slope
        if len(self.temp_history) < 120:
            return None
        
        # Calculate slope between current and 5-6 minutes ago
        now = datetime.utcnow()
        five_min_ago = now - timedelta(minutes=5)
        six_min_ago = now - timedelta(minutes=6)
        
        # Find average temperature in 5-6 minute window
        historical_temps = [
            temp for timestamp, temp in self.temp_history
            if six_min_ago <= timestamp <= five_min_ago
        ]
        
        if not historical_temps:
            return None
        
        historical_avg = statistics.mean(historical_temps)
        
        # Calculate slope (°C/min)
        time_diff_min = 5.0  # 5 minutes difference
        slope = (current_temp - historical_avg) / time_diff_min
        
        return slope
    
    def _calculate_stability_metric(self, field_name: str) -> Optional[float]:
        """Calculate standard deviation over last 60 seconds"""
        if len(self.reading_buffer) < 10:  # Need minimum samples
            return None
        
        # Get last 60 seconds of data
        now = datetime.utcnow()
        sixty_sec_ago = now - timedelta(seconds=60)
        
        values = []
        for reading in self.reading_buffer:
            if reading.timestamp >= sixty_sec_ago:
                value = getattr(reading, field_name, None)
                if value is not None:
                    values.append(value)
        
        if len(values) < 5:  # Need minimum samples for stability
            return None
        
        return statistics.stdev(values) if len(values) > 1 else 0.0
    
    def _detect_sensor_fault(self, reading: SensorReading, metrics: DerivedMetrics) -> bool:
        """Detect sensor faults and invalid data"""
        # Check for implausible temperatures
        temps = [reading.temp_zone_1, reading.temp_zone_2, reading.temp_zone_3, reading.temp_zone_4]
        valid_temps = [t for t in temps if t is not None]
        
        # Temperature faults
        if valid_temps:
            if any(t <= 0 or t < -20 for t in valid_temps):
                return True
            if any(t > 400 for t in valid_temps):  # Unlikely for extruder
                return True
        
        # Pressure fault (exactly 0 while RPM is high)
        if (reading.pressure_bar == 0 and reading.screw_rpm and 
            reading.screw_rpm > self.thresholds.RPM_PROD):
            return True
        
        # Missing critical data
        if reading.screw_rpm is None:
            return True
        
        # Too many missing temperature zones
        if len(valid_temps) < 2:  # At least 2 zones needed
            return True
        
        # Invalid timestamp (should be handled by caller, but double-check)
        if reading.timestamp > datetime.utcnow() + timedelta(minutes=1):
            return True
        
        return False
    
    def _determine_state(self, reading: SensorReading, metrics: DerivedMetrics) -> Tuple[MachineState, float]:
        """Determine machine state based on current readings"""
        rpm = reading.screw_rpm or 0.0
        pressure = reading.pressure_bar or 0.0
        temp_avg = metrics.temp_avg or 0.0
        d_temp = metrics.d_temp_avg or 0.0
        
        logger.debug("State determination: machine_id={}, rpm={}, pressure={}, temp_avg={}", 
                    self.machine_id, rpm, pressure, temp_avg)
        
        # OFF: cold, no RPM, no pressure
        if (rpm < self.thresholds.RPM_ON and 
            pressure < self.thresholds.P_ON and 
            temp_avg < self.thresholds.T_MIN_ACTIVE):
            logger.debug("OFF state detected: machine_id={}", self.machine_id)
            return MachineState.OFF, 0.9
        
        # COOLING: RPM off, temperature falling
        if (rpm < self.thresholds.RPM_ON and 
            d_temp <= self.thresholds.COOLING_RATE and 
            temp_avg >= self.thresholds.T_MIN_ACTIVE):
            return MachineState.COOLING, 0.8
        
        # HEATING: temperature rising, no production
        if (rpm < self.thresholds.RPM_PROD and 
            d_temp >= self.thresholds.HEATING_RATE and 
            temp_avg >= self.thresholds.T_MIN_ACTIVE):
            return MachineState.HEATING, 0.8
        
        # PRODUCTION: primary criteria
        if (rpm >= self.thresholds.RPM_PROD and 
            pressure >= self.thresholds.P_PROD):
            logger.info("PRODUCTION state detected (primary): machine_id={}, rpm={}, pressure={}", 
                       self.machine_id, rpm, pressure)
            return MachineState.PRODUCTION, 0.9
        
        # PRODUCTION: fallback criteria
        if rpm >= self.thresholds.RPM_PROD:
            fallback_conditions = []
            
            # Check pressure
            if pressure >= self.thresholds.P_ON:
                fallback_conditions.append("pressure")
            
            # Check motor load
            if reading.motor_load and reading.motor_load >= self.thresholds.MOTOR_LOAD_MIN:
                fallback_conditions.append("motor_load")
            
            # Check throughput
            if reading.throughput_kg_h and reading.throughput_kg_h >= self.thresholds.THROUGHPUT_MIN:
                fallback_conditions.append("throughput")
            
            if fallback_conditions:
                confidence = 0.7 if len(fallback_conditions) > 1 else 0.6
                return MachineState.PRODUCTION, confidence
        
        # IDLE: warm, stable, no production
        if (rpm < self.thresholds.RPM_ON and 
            pressure < self.thresholds.P_ON and 
            temp_avg >= self.thresholds.T_MIN_ACTIVE and 
            abs(d_temp) < self.thresholds.TEMP_FLAT_RATE):
            return MachineState.IDLE, 0.8
        
        # Default to IDLE if warm but uncertain
        if temp_avg >= self.thresholds.T_MIN_ACTIVE:
            return MachineState.IDLE, 0.5
        
        # Default to OFF
        return MachineState.OFF, 0.4
    
    def _apply_hysteresis(self, new_state: MachineState, confidence: float) -> Tuple[MachineState, float]:
        """Apply hysteresis and debounce logic"""
        current = self.current_state.state
        
        # No change - return current state
        if new_state == current:
            return current, confidence
        
        # Special handling for PRODUCTION (requires 90s)
        if new_state == MachineState.PRODUCTION:
            timer_name = f"enter_production_{self.machine_id}"
            
            if not self.timer.is_timer_expired(timer_name):
                # Still waiting for timer
                return current, confidence
            
            # Check if we've been in production-like state for 90s
            state_duration = self.timer.get_state_duration(current)
            if state_duration.total_seconds() >= self.thresholds.PRODUCTION_ENTER_TIME:
                # Can enter production
                self.timer.clear_timer(timer_name)
                return new_state, confidence
            else:
                # Start timer if not already running
                if timer_name not in self.timer.timers:
                    remaining_time = self.thresholds.PRODUCTION_ENTER_TIME - state_duration.total_seconds()
                    self.timer.start_timer(timer_name, int(remaining_time))
                return current, confidence
        
        # Exiting production (requires 120s)
        elif current == MachineState.PRODUCTION and new_state != MachineState.PRODUCTION:
            timer_name = f"exit_production_{self.machine_id}"
            
            if not self.timer.is_timer_expired(timer_name):
                return current, confidence
            
            # Check if we've been out of production criteria for 120s
            # This is handled by checking recent readings in the state determination
            self.timer.clear_timer(timer_name)
            return new_state, confidence
        
        # Other state changes (60s debounce)
        else:
            timer_name = f"state_change_{self.machine_id}"
            
            if not self.timer.is_timer_expired(timer_name):
                return current, confidence
            
            self.timer.clear_timer(timer_name)
            return new_state, confidence
    
    def get_current_state(self) -> MachineStateInfo:
        """Get current machine state"""
        return self.current_state
    
    def is_in_production(self) -> bool:
        """Check if machine is currently in PRODUCTION state"""
        return self.current_state.state == MachineState.PRODUCTION
    
    def get_state_duration(self) -> timedelta:
        """Get duration of current state"""
        return self.timer.get_state_duration(self.current_state.state)

# Global registry for machine state detectors
_machine_detectors: Dict[str, MachineStateDetector] = {}

def get_machine_detector(machine_id: str, thresholds: Optional[StateThresholds] = None) -> MachineStateDetector:
    """Get or create machine state detector for a machine"""
    if machine_id not in _machine_detectors:
        _machine_detectors[machine_id] = MachineStateDetector(machine_id, thresholds)
    return _machine_detectors[machine_id]

def remove_machine_detector(machine_id: str):
    """Remove machine state detector"""
    _machine_detectors.pop(machine_id, None)

def get_all_machine_states() -> Dict[str, MachineStateInfo]:
    """Get current states of all machines"""
    return {machine_id: detector.get_current_state() 
            for machine_id, detector in _machine_detectors.items()}

async def process_sensor_data_for_state(
    session, machine_id: str, sensor_type: str, value: float, timestamp: datetime
):
    """Process incoming sensor data for machine state detection"""
    try:
        # Get or create detector for this machine
        detector = get_machine_detector(machine_id)
        
        # Map sensor types to detector fields
        sensor_mapping = {
            'temperature': 'temp_zone_1',  # Use zone 1 for general temperature
            'pressure': 'pressure_bar',
            'vibration': None,  # Not directly mapped, but could affect derived metrics
            'motor_current': 'motor_load',
            'rpm': 'screw_rpm'
        }
        
        field_name = sensor_mapping.get(sensor_type.lower())
        if field_name:
            # Create sensor reading with the new value
            current_state = detector.get_current_state()
            
            # Get existing sensor data or create new reading
            reading = SensorReading(timestamp=timestamp)
            
            # Update the specific field
            if field_name == 'temp_zone_1':
                reading.temp_zone_1 = value
            elif field_name == 'pressure_bar':
                reading.pressure_bar = value
            elif field_name == 'motor_load':
                reading.motor_load = value
            elif field_name == 'screw_rpm':
                reading.screw_rpm = value
            
            # Process the reading for state detection
            detector.process_reading(reading)
            
            # Store state in database if changed
            new_state = detector.get_current_state()
            if new_state.state != current_state.state:
                await store_machine_state_in_db(session, machine_id, new_state)
                
    except Exception as e:
        logger.error(f"Error processing sensor data for machine state: {e}")

async def store_machine_state_in_db(session, machine_id: str, state_info: MachineStateInfo):
    """Store machine state transition in database"""
    try:
        from app.models.machine_state import MachineState, MachineStateEnum
        
        # Create machine state record
        machine_state = MachineState(
            machine_id=machine_id,
            state=MachineStateEnum(state_info.state.value),
            confidence=state_info.confidence,
            state_since=state_info.state_since,
            last_updated=state_info.last_updated,
            metrics=state_info.metrics.__dict__ if state_info.metrics else {},
            flags=state_info.flags or {}
        )
        
        session.add(machine_state)
        await session.flush()  # Get ID without committing
        
        logger.info(f"Stored machine state transition: {machine_id} -> {state_info.state.value}")
        
    except Exception as e:
        logger.error(f"Error storing machine state in database: {e}")
