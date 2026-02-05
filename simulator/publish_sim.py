import json
import os
import random
import time
import math
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))

# Enhanced simulator with multiple machines and diverse sensors
MACHINES = [
    {
        "machine_id": "machine-1",
        "name": "Pump-01",
        "location": "Building A, Floor 2",
        "topic": "factory/demo/line1/machine1/sensors",
        "sensors": [
            {"sensor_id": "pressure-head", "name": "pressure", "unit": "psi", "min": 100, "max": 180, "normal": 140},
            {"sensor_id": "temp-core", "name": "temperature", "unit": "°C", "min": 200, "max": 260, "normal": 230},
            {"sensor_id": "vibe-x", "name": "vibration", "unit": "mm/s", "min": 2, "max": 5, "normal": 3.5},
            {"sensor_id": "flow-rate", "name": "flow", "unit": "L/min", "min": 50, "max": 150, "normal": 100},
        ]
    },
    {
        "machine_id": "machine-2",
        "name": "Motor-02",
        "location": "Building B, Floor 1",
        "topic": "factory/demo/line2/machine2/sensors",
        "sensors": [
            {"sensor_id": "current-phase-a", "name": "current", "unit": "A", "min": 10, "max": 50, "normal": 30},
            {"sensor_id": "temp-winding", "name": "temperature", "unit": "°C", "min": 60, "max": 120, "normal": 85},
            {"sensor_id": "vibration-base", "name": "vibration", "unit": "mm/s", "min": 1, "max": 4, "normal": 2.5},
            {"sensor_id": "rpm-shaft", "name": "rpm", "unit": "rpm", "min": 1400, "max": 1600, "normal": 1500},
        ]
    },
    {
        "machine_id": "machine-3",
        "name": "Compressor-A",
        "location": "Building C, Floor 3",
        "topic": "factory/demo/line3/machine3/sensors",
        "sensors": [
            {"sensor_id": "pressure-tank", "name": "pressure", "unit": "bar", "min": 6, "max": 10, "normal": 8},
            {"sensor_id": "temp-discharge", "name": "temperature", "unit": "°C", "min": 40, "max": 90, "normal": 65},
            {"sensor_id": "oil-level", "name": "oil_level", "unit": "%", "min": 40, "max": 100, "normal": 80},
            {"sensor_id": "vibration-1", "name": "vibration", "unit": "mm/s", "min": 1.5, "max": 4.5, "normal": 3},
        ]
    },
    {
        "machine_id": "machine-4",
        "name": "Conveyor-B2",
        "location": "Building B, Floor 2",
        "topic": "factory/demo/line2/conveyor/sensors",
        "sensors": [
            {"sensor_id": "speed-belt", "name": "speed", "unit": "m/s", "min": 0.5, "max": 2.5, "normal": 1.5},
            {"sensor_id": "load-weight", "name": "load", "unit": "kg", "min": 0, "max": 500, "normal": 250},
            {"sensor_id": "temp-bearing", "name": "temperature", "unit": "°C", "min": 25, "max": 70, "normal": 45},
            {"sensor_id": "torque-motor", "name": "torque", "unit": "Nm", "min": 50, "max": 200, "normal": 125},
        ]
    },
]

# Enhanced anomaly patterns for full device simulation
# States: normal (70%), warning (20%), critical (10%) - More realistic distribution
ANOMALY_PATTERNS = {
    "normal": {"chance": 0.70, "variation": 0.05},
    "warning": {"chance": 0.20, "max_offset": 0.20},
    "critical": {"chance": 0.10, "max_offset": 0.40},
    "gradual_drift": {"chance": 0.02, "max_offset": 0.15},
    "sudden_spike": {"chance": 0.01, "multiplier": 1.5},
    "oscillation": {"chance": 0.015, "amplitude": 0.1},
}

# Device state machine for realistic simulation - More frequent state changes
DEVICE_STATES = {
    "normal": {"duration_range": (20, 80), "next_states": ["warning", "normal"]},  # Shorter normal duration
    "warning": {"duration_range": (5, 20), "next_states": ["critical", "normal", "warning"]},  # Can stay in warning
    "critical": {"duration_range": (3, 10), "next_states": ["warning", "normal"]},  # Shorter critical, can recover
}

# Track state for each sensor for anomaly simulation
sensor_states = {}


def generate_value(sensor, machine_id, sensor_id, cycle_time):
    """Generate realistic sensor value with occasional anomalies"""
    key = f"{machine_id}:{sensor_id}"
    
    # Initialize state if needed with device state machine
    if key not in sensor_states:
        sensor_states[key] = {
            "base_value": sensor.get("normal", (sensor["min"] + sensor["max"]) / 2),
            "drift": 0,
            "anomaly_active": False,
            "anomaly_type": None,
            "cycle_count": 0,
            "device_state": "normal",  # normal, warning, critical
            "state_duration": 0,
            "state_target_duration": random.randint(*DEVICE_STATES["normal"]["duration_range"]),
        }
    
    state = sensor_states[key]
    state["cycle_count"] += 1
    state["state_duration"] += 1
    
    # Device state machine - transition between normal/warning/critical
    # Force more frequent state changes to show warnings/critical
    if state["state_duration"] >= state["state_target_duration"]:
        # Transition to next state
        current_state = state["device_state"]
        next_states = DEVICE_STATES[current_state]["next_states"]
        
        # Bias towards warning/critical states (70% chance to transition to warning/critical from normal)
        if current_state == "normal" and random.random() < 0.7:
            # Prefer warning over critical (60% warning, 40% critical)
            state["device_state"] = "warning" if random.random() < 0.6 else "critical"
        else:
            state["device_state"] = random.choice(next_states)
        
        state["state_duration"] = 0
        state["state_target_duration"] = random.randint(*DEVICE_STATES[state["device_state"]]["duration_range"])
    
    # Normal operation with small random variations
    normal_range = sensor["max"] - sensor["min"]
    drift_variation = random.uniform(-normal_range * 0.02, normal_range * 0.02)
    
    # Add gradual drift over time (simulating wear)
    if random.random() < 0.1:  # 10% chance to adjust drift
        state["drift"] += random.uniform(-normal_range * 0.001, normal_range * 0.001)
        state["drift"] = max(-normal_range * 0.05, min(normal_range * 0.05, state["drift"]))
    
    # Apply device state to value
    device_state = state["device_state"]
    base_value = state["base_value"] + drift_variation + state["drift"]
    
    # Map sensor names to AI service thresholds for proper detection
    sensor_name_lower = sensor.get("name", "").lower()
    is_pressure = "pressure" in sensor_name_lower
    is_temperature = "temp" in sensor_name_lower or "temperature" in sensor_name_lower
    is_vibration = "vibration" in sensor_name_lower or "vib" in sensor_name_lower
    is_current = "current" in sensor_name_lower
    
    if device_state == "warning":
        # Warning: Generate values that exceed AI service warning thresholds
        if is_pressure:
            # AI threshold: warn: 150.0, alarm: 180.0
            value = random.uniform(150.0, 179.0)  # Between warn and alarm
        elif is_temperature:
            # AI threshold: warn: 250.0, alarm: 280.0
            value = random.uniform(250.0, 279.0)
        elif is_vibration:
            # AI threshold: warn: 4.0, alarm: 6.0
            value = random.uniform(4.0, 5.9)
        elif is_current:
            # AI threshold: warn: 18.0, alarm: 22.0
            value = random.uniform(18.0, 21.9)
        else:
            # Generic warning: 25-40% deviation
            warning_offset = normal_range * random.uniform(0.25, 0.40)
            value = base_value + warning_offset
    elif device_state == "critical":
        # Critical: Generate values that exceed AI service alarm thresholds
        if is_pressure:
            # AI threshold: alarm: 180.0
            value = random.uniform(180.0, 220.0)  # Above alarm threshold
        elif is_temperature:
            # AI threshold: alarm: 280.0
            value = random.uniform(280.0, 320.0)
        elif is_vibration:
            # AI threshold: alarm: 6.0
            value = random.uniform(6.0, 8.0)
        elif is_current:
            # AI threshold: alarm: 22.0
            value = random.uniform(22.0, 28.0)
        else:
            # Generic critical: 50-80% deviation
            critical_offset = normal_range * random.uniform(0.50, 0.80)
            value = base_value + critical_offset * 1.5
    else:
        # Normal: small variation, well below thresholds
        value = base_value
    
    # Check for anomaly events (reduced frequency - 90% normal, 10% anomalies)
    if not state["anomaly_active"]:
        anomaly_roll = random.random()
        # Reduce anomaly chance to 10% (was ~4.5%) - so 90% normal predictions
        if anomaly_roll < 0.01:  # 1% chance for gradual drift
            state["anomaly_active"] = True
            state["anomaly_type"] = "gradual_drift"
            state["anomaly_duration"] = random.randint(20, 60)  # 20-60 cycles
        elif anomaly_roll < 0.02:  # 1% chance for sudden spike
            state["anomaly_active"] = True
            state["anomaly_type"] = "sudden_spike"
            state["anomaly_duration"] = random.randint(5, 15)
        elif anomaly_roll < 0.03:  # 1% chance for oscillation
            state["anomaly_active"] = True
            state["anomaly_type"] = "oscillation"
            state["anomaly_duration"] = random.randint(15, 30)
            state["oscillation_phase"] = 0
        # 97% of the time, values stay normal
    
    # Apply active anomaly
    if state["anomaly_active"]:
        if state["anomaly_type"] == "gradual_drift":
            max_offset = normal_range * ANOMALY_PATTERNS["gradual_drift"]["max_offset"]
            value += max_offset * (1 - state["anomaly_duration"] / 100)  # Gradually increasing
            state["anomaly_duration"] -= 1
        elif state["anomaly_type"] == "sudden_spike":
            spike = normal_range * 0.3 * ANOMALY_PATTERNS["sudden_spike"]["multiplier"]
            value += spike * random.uniform(0.8, 1.2)
            state["anomaly_duration"] -= 1
        elif state["anomaly_type"] == "oscillation":
            amplitude = normal_range * ANOMALY_PATTERNS["oscillation"]["amplitude"]
            state["oscillation_phase"] += 0.5
            value += amplitude * math.sin(state["oscillation_phase"])
            state["anomaly_duration"] -= 1
        
        if state["anomaly_duration"] <= 0:
            state["anomaly_active"] = False
            state["anomaly_type"] = None
    
    # Clamp to sensor range with occasional over-limit values (realistic anomalies)
    if state["anomaly_active"] and random.random() < 0.3:
        # Allow values outside normal range during anomalies
        pass
    else:
        value = max(sensor["min"] * 0.9, min(sensor["max"] * 1.1, value))
    
    return round(value, 2)


def main():
    print(f"🚀 Starting Predictive Maintenance Simulator...")
    print(f"📍 MQTT Broker: {MQTT_HOST}:{MQTT_PORT}")
    
    client = mqtt.Client(client_id=f"simulator-{random.randint(1000, 9999)}")
    
    # Connection callbacks
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
        else:
            print(f"❌ Connection failed with return code {rc}")
    
    def on_disconnect(client, userdata, rc):
        if rc != 0:
            print(f"⚠️ Unexpected disconnection from MQTT broker (rc: {rc})")
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    
    # Wait for MQTT broker to be available with retries
    max_retries = 30
    retry_count = 0
    connected = False
    
    while not connected and retry_count < max_retries:
        try:
            print(f"🔄 Attempting to connect to MQTT broker at {MQTT_HOST}:{MQTT_PORT} (attempt {retry_count + 1}/{max_retries})...")
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            client.loop_start()
            time.sleep(3)  # Wait for connection callback
            
            if client.is_connected():
                connected = True
                print(f"✅ Simulator ready - Connected to MQTT {MQTT_HOST}:{MQTT_PORT}")
            else:
                raise Exception("Connection not established after callback")
        except Exception as e:
            retry_count += 1
            print(f"⚠️ Connection attempt {retry_count} failed: {e}")
            if retry_count < max_retries:
                print(f"   Retrying in 3 seconds...")
                time.sleep(3)
            else:
                print(f"❌ Failed to connect after {max_retries} attempts")
                print(f"   Please check:")
                print(f"   - MQTT broker is running")
                print(f"   - MQTT_BROKER_HOST is set correctly (current: {MQTT_HOST})")
                print(f"   - Network connectivity")
                return
    
    if not connected:
        print("❌ Could not establish MQTT connection. Exiting.")
        return
    
    try:
        print(f"📊 Simulating {len(MACHINES)} machines with {sum(len(m['sensors']) for m in MACHINES)} sensors")
        
        cycle_time = 0
        
        while True:
            cycle_time += 1
            
            for machine in MACHINES:
                for sensor in machine["sensors"]:
                    value = generate_value(sensor, machine["machine_id"], sensor["sensor_id"], cycle_time)
                    
                    # Get device state for this sensor
                    sensor_key = f"{machine['machine_id']}:{sensor['sensor_id']}"
                    device_state = sensor_states.get(sensor_key, {}).get("device_state", "normal")
                    
                    payload = {
                        "sensor_id": sensor["sensor_id"],
                        "machine_id": machine["machine_id"],
                        "metric": sensor["name"],
                        "value": value,
                        "unit": sensor.get("unit", ""),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "location": machine.get("location", ""),
                        "status": device_state,  # normal, warning, critical
                        "metadata": {
                            "machine_name": machine["name"],
                            "sensor_type": sensor["name"],
                            "cycle": cycle_time,
                            "device_state": device_state,
                            "state_duration": sensor_states.get(sensor_key, {}).get("state_duration", 0),
                        }
                    }
                    
                    client.publish(machine["topic"], json.dumps(payload))
                    
                    # Log anomalies for debugging
                    key = f"{machine['machine_id']}:{sensor['sensor_id']}"
                    state = sensor_states.get(key, {})
                    if state.get("anomaly_active"):
                        print(f"⚠️  ANOMALY: {machine['name']} - {sensor['name']} = {value} ({state.get('anomaly_type')})")
            
            # Small delay between cycles
            time.sleep(0.5)
            
            # Progress indicator every 100 cycles
            if cycle_time % 100 == 0:
                print(f"📈 Cycle {cycle_time}: Published {cycle_time * sum(len(m['sensors']) for m in MACHINES)} sensor readings")
                
    except KeyboardInterrupt:
        print("\n🛑 Simulator stopped by user")
        if client and client.is_connected():
            client.loop_stop()
            client.disconnect()
    except Exception as e:
        print(f"❌ Error in main loop: {e}")
        import traceback
        traceback.print_exc()
        # Try to reconnect
        print("🔄 Attempting to reconnect in 5 seconds...")
        time.sleep(5)
        main()  # Restart the simulator
    finally:
        if client and client.is_connected():
            client.loop_stop()
            client.disconnect()


if __name__ == "__main__":
    main()
