"""
Direct sensor data simulator for machine state detection
Generates realistic sensor data that follows machine state patterns
"""

import asyncio
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.machine import Machine
from app.models.sensor import Sensor
from app.models.sensor_data import SensorData
from app.services.machine_state_service import (
    MachineState, get_machine_detector, process_sensor_data_for_state
)


class SensorDataSimulator:
    """Simulates realistic sensor data for machine state detection"""
    
    def __init__(self):
        self.machine_states: Dict[str, MachineState] = {}
        self.state_start_times: Dict[str, datetime] = {}
        self.running = False
        
        # Machine state configurations with realistic sensor values
        self.state_configs = {
            MachineState.OFF: {
                'rpm': (0, 50),           # Very low RPM
                'pressure': (0.1, 0.5),   # Near atmospheric
                'temperature': (20, 30), # Room temperature
                'vibration': (0.1, 0.5), # Minimal vibration
                'motor_current': (0.1, 1.0) # Minimal current
            },
            MachineState.HEATING: {
                'rpm': (100, 300),        # Low RPM, warming up
                'pressure': (1.0, 2.0),   # Building pressure
                'temperature': (40, 80),  # Rising temperature
                'vibration': (1.0, 2.0), # Low vibration
                'motor_current': (5, 15)  # Moderate current
            },
            MachineState.IDLE: {
                'rpm': (300, 500),        # Medium RPM, ready
                'pressure': (2.0, 3.0),   # Stable pressure
                'temperature': (70, 90),  # Operating temperature
                'vibration': (2.0, 3.0), # Moderate vibration
                'motor_current': (10, 20) # Stable current
            },
            MachineState.PRODUCTION: {
                'rpm': (800, 1200),       # High RPM, producing
                'pressure': (4.0, 6.0),   # High pressure
                'temperature': (85, 110), # High temperature
                'vibration': (4.0, 6.0),  # High vibration
                'motor_current': (25, 40) # High current
            },
            MachineState.COOLING: {
                'rpm': (200, 400),        # Decreasing RPM
                'pressure': (1.5, 2.5),   # Decreasing pressure
                'temperature': (60, 85),  # Cooling down
                'vibration': (1.5, 2.5), # Decreasing vibration
                'motor_current': (8, 15)  # Decreasing current
            }
        }
        
        # State transition probabilities and durations
        self.state_transitions = {
            MachineState.OFF: {
                MachineState.HEATING: 0.3,    # 30% chance to start heating
                MachineState.OFF: 0.7          # 70% chance to stay off
            },
            MachineState.HEATING: {
                MachineState.IDLE: 0.4,        # 40% chance to reach idle
                MachineState.HEATING: 0.5,     # 50% chance to continue heating
                MachineState.OFF: 0.1         # 10% chance to fail and turn off
            },
            MachineState.IDLE: {
                MachineState.PRODUCTION: 0.3, # 30% chance to start production
                MachineState.OFF: 0.2,        # 20% chance to turn off
                MachineState.IDLE: 0.5        # 50% chance to stay idle
            },
            MachineState.PRODUCTION: {
                MachineState.COOLING: 0.2,    # 20% chance to start cooling
                MachineState.IDLE: 0.1,        # 10% chance to go back to idle
                MachineState.PRODUCTION: 0.7  # 70% chance to continue production
            },
            MachineState.COOLING: {
                MachineState.OFF: 0.4,         # 40% chance to turn off
                MachineState.IDLE: 0.3,       # 30% chance to go to idle
                MachineState.COOLING: 0.3     # 30% chance to continue cooling
            }
        }
        
        # Minimum state durations (in seconds) to prevent rapid switching
        self.min_state_durations = {
            MachineState.OFF: 60,
            MachineState.HEATING: 90,
            MachineState.IDLE: 60,
            MachineState.PRODUCTION: 120,
            MachineState.COOLING: 60
        }

    async def get_machines_and_sensors(self) -> Dict[str, List[Sensor]]:
        """Get all machines and their sensors"""
        async with AsyncSessionLocal() as session:
            machines_result = await session.execute(select(Machine))
            machines = machines_result.scalars().all()
            
            machines_sensors = {}
            for machine in machines:
                sensors_result = await session.execute(
                    select(Sensor).where(Sensor.machine_id == machine.id)
                )
                sensors = sensors_result.scalars().all()
                machines_sensors[machine.id] = sensors
                
                # Initialize machine state if not exists
                if machine.id not in self.machine_states:
                    self.machine_states[machine.id] = MachineState.OFF
                    self.state_start_times[machine.id] = datetime.utcnow()
                    
        return machines_sensors

    def generate_sensor_value(self, sensor_type: str, state: MachineState) -> float:
        """Generate realistic sensor value based on machine state"""
        config = self.state_configs[state]
        
        # Map sensor types to config keys
        sensor_mapping = {
            'temperature': 'temperature',
            'temperature sensor': 'temperature',
            'pressure': 'pressure',
            'pressure sensor': 'pressure',
            'vibration': 'vibration',
            'vibration sensor': 'vibration',
            'motor_current': 'motor_current',
            'motor current': 'motor_current',
            'motor current sensor': 'motor_current',
            'rpm': 'rpm',
            'rpm sensor': 'rpm',
            'speed sensor': 'rpm',
            'load sensor': 'motor_current',
            'current sensor': 'motor_current',
            'torque sensor': 'motor_current',
            'flow sensor': 'pressure',
            'oil level sensor': 'pressure'
        }
        
        config_key = sensor_mapping.get(sensor_type.lower(), 'temperature')
        min_val, max_val = config.get(config_key, (20, 30))
        
        # Add some randomness within the range
        value = random.uniform(min_val, max_val)
        
        # Add small noise for realism
        noise = random.gauss(0, (max_val - min_val) * 0.02)
        value += noise
        
        return round(value, 2)

    def should_transition_state(self, machine_id: str) -> bool:
        """Check if machine should transition to a new state"""
        current_state = self.machine_states[machine_id]
        state_start = self.state_start_times[machine_id]
        time_in_state = (datetime.utcnow() - state_start).total_seconds()
        
        # Check minimum duration
        min_duration = self.min_state_durations.get(current_state, 60)
        if time_in_state < min_duration:
            return False
            
        # Check transition probability
        transitions = self.state_transitions.get(current_state, {})
        rand = random.random()
        cumulative = 0.0
        
        for new_state, probability in transitions.items():
            cumulative += probability
            if rand <= cumulative:
                self.machine_states[machine_id] = new_state
                self.state_start_times[machine_id] = datetime.utcnow()
                logger.info(f"Machine {machine_id} transitioned from {current_state} to {new_state}")
                return True
                
        return False

    async def generate_sensor_data(self, machines_sensors: Dict[str, List[Sensor]]):
        """Generate sensor data for all machines"""
        timestamp = datetime.utcnow()
        
        async with AsyncSessionLocal() as session:
            for machine_id, sensors in machines_sensors.items():
                # Check if we should transition state
                self.should_transition_state(machine_id)
                current_state = self.machine_states[machine_id]
                
                for sensor in sensors:
                    # Generate realistic sensor value
                    value = self.generate_sensor_value(sensor.name, current_state)
                    
                    # Create sensor data record
                    sensor_data = SensorData(
                        sensor_id=sensor.id,
                        machine_id=machine_id,
                        value=value,
                        timestamp=timestamp
                    )
                    
                    session.add(sensor_data)
                    
                    # Process for machine state detection
                    logger.info(f"About to process sensor data for state: machine_id={machine_id}, sensor={sensor.name}, value={value}")
                    await process_sensor_data_for_state(
                        session, machine_id, sensor.name, value, timestamp
                    )
                    logger.info(f"Finished processing sensor data for state: machine_id={machine_id}, sensor={sensor.name}")
            
            await session.commit()
            
        logger.debug(f"Generated sensor data for {len(machines_sensors)} machines in state {self.machine_states}")

    async def start_simulation(self, interval_seconds: int = 2):
        """Start the sensor data simulation"""
        logger.info("Starting sensor data simulation...")
        self.running = True
        
        # Get machines and sensors
        machines_sensors = await self.get_machines_and_sensors()
        
        if not machines_sensors:
            logger.warning("No machines or sensors found. Creating demo data...")
            # Create demo machines and sensors if none exist
            await self.create_demo_data()
            machines_sensors = await self.get_machines_and_sensors()
        
        logger.info(f"Starting simulation for {len(machines_sensors)} machines")
        
        while self.running:
            try:
                await self.generate_sensor_data(machines_sensors)
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in sensor data simulation: {e}")
                await asyncio.sleep(interval_seconds)

    async def create_demo_data(self):
        """Create demo machines and sensors for testing"""
        async with AsyncSessionLocal() as session:
            # Create demo machines
            machines = [
                Machine(name="Extruder-01", location="Production Line A", status="active"),
                Machine(name="Pump-02", location="Production Line B", status="active"),
                Machine(name="Compressor-A", location="Utility Area", status="active")
            ]
            
            for machine in machines:
                session.add(machine)
            await session.flush()  # Get IDs
                
            # Create sensors for each machine
            sensor_types = [
                ("Temperature", "temperature", "°C"),
                ("Pressure", "pressure", "bar"),
                ("Vibration", "vibration", "Hz"),
                ("Motor Current", "motor_current", "A"),
                ("RPM", "rpm", "rpm")
            ]
            
            for machine in machines:
                for sensor_name, sensor_type, unit in sensor_types:
                    sensor = Sensor(
                        machine_id=machine.id,
                        name=sensor_name,
                        sensor_type=sensor_type,
                        unit=unit,
                        min_value=0,
                        max_value=1000,
                        warning_threshold=80,
                        critical_threshold=95
                    )
                    session.add(sensor)
            
            await session.commit()
            logger.info("Created demo machines and sensors")

    def stop(self):
        """Stop the simulation"""
        self.running = False
        logger.info("Sensor data simulation stopped")


# Global simulator instance
_simulator = None

async def start_sensor_data_simulation(interval_seconds: int = 2):
    """Start the sensor data simulation"""
    global _simulator
    if _simulator is None:
        _simulator = SensorDataSimulator()
    
    await _simulator.start_simulation(interval_seconds)

def stop_sensor_data_simulation():
    """Stop the sensor data simulation"""
    global _simulator
    if _simulator:
        _simulator.stop()
