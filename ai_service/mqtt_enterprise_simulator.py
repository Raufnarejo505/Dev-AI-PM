# mqtt_enterprise_simulator.py
import paho.mqtt.client as mqtt
import json
import time
import random
import argparse
import sys

class EnterpriseSimulator:
    def __init__(self, broker_url):
        self.broker_url = broker_url
        self.client = mqtt.Client(client_id="enterprise_simulator", protocol=mqtt.MQTTv5)
        self.running = False
        
        # Parse broker URL
        if broker_url.startswith("mqtts://"):
            self.use_tls = True
            broker_url = broker_url[8:]
            if ":" in broker_url:
                self.host, port_str = broker_url.split(":", 1)
                self.port = int(port_str)
            else:
                self.host = broker_url
                self.port = 8883
        else:
            self.use_tls = False
            broker_url = broker_url[6:] if broker_url.startswith("mqtt://") else broker_url
            if ":" in broker_url:
                self.host, port_str = broker_url.split(":", 1)
                self.port = int(port_str)
            else:
                self.host = broker_url
                self.port = 1883
    
    def connect(self):
        try:
            if self.use_tls:
                self.client.tls_set()
            
            self.client.connect(self.host, self.port, 60)
            self.client.loop_start()
            print(f"✅ Connected to MQTT broker: {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    def simulate_normal_operation(self, duration=60):
        """Simulate normal industrial operation"""
        print("🏭 Starting NORMAL Operation Simulation...")
        self.running = True
        start_time = time.time()
        message_count = 0
        
        while self.running and (time.time() - start_time) < duration:
            # Simulate multiple machines
            machines = [
                {"tenant": "tenantA", "site": "site1", "line": "lineA", "machine": "extruder_01"},
                {"tenant": "tenantA", "site": "site1", "line": "lineA", "machine": "extruder_02"},
            ]
            
            for machine in machines:
                # Normal sensor values with small noise
                sensors = {
                    "pressure": 105 + random.uniform(-3, 3),
                    "temperature": 210 + random.uniform(-2, 2),
                    "motor_current": 12 + random.uniform(-0.5, 0.5)
                }
                
                for sensor_name, value in sensors.items():
                    topic = f"tenant/{machine['tenant']}/site/{machine['site']}/{machine['line']}/{machine['machine']}/sensor/{sensor_name}"
                    
                    payload = {
                        "tenant": machine['tenant'],
                        "site": machine['site'],
                        "line": machine['line'],
                        "machine": machine['machine'],
                        "sensor": sensor_name,
                        "value": round(value, 2),
                        "timestamp": int(time.time()),
                        "seq": message_count
                    }
                    
                    self.client.publish(topic, json.dumps(payload), qos=1)
                    message_count += 1
                    print(f"📤 {sensor_name}: {value:.1f} (Normal)")
            
            time.sleep(2)  # Send every 2 seconds
        
        print(f"✅ Normal simulation completed: {message_count} messages sent")
    
    def simulate_anomalies(self):
        """Simulate various anomaly scenarios"""
        print("\n🚨 Starting ANOMALY Simulation...")
        
        # Scenario 1: Critical pressure drop
        print("🔴 Simulating CRITICAL LOW PRESSURE...")
        self._publish_anomaly("extruder_01", "pressure", 50, "CRITICAL_LOW")
        time.sleep(3)
        
        # Scenario 2: Critical temperature spike
        print("🔴 Simulating CRITICAL HIGH TEMPERATURE...")
        self._publish_anomaly("extruder_02", "temperature", 350, "CRITICAL_HIGH")
        time.sleep(3)
        
        # Scenario 3: Drift scenario
        print("📈 Simulating PRESSURE DRIFT...")
        base_pressure = 100
        for i in range(10):
            pressure = base_pressure + (i * 4)  # Increasing drift
            self._publish_anomaly("extruder_01", "pressure", pressure, f"DRIFT_{i}")
            time.sleep(1)
        
        print("✅ Anomaly simulation completed")
    
    def _publish_anomaly(self, machine, sensor, value, scenario):
        topic = f"tenant/tenantA/site/site1/line/lineA/{machine}/sensor/{sensor}"
        
        payload = {
            "tenant": "tenantA",
            "site": "site1",
            "line": "lineA",
            "machine": machine,
            "sensor": sensor,
            "value": value,
            "timestamp": int(time.time()),
            "scenario": scenario
        }
        
        self.client.publish(topic, json.dumps(payload), qos=1)
        print(f"📤 {sensor} ANOMALY: {value} ({scenario})")
    
    def stop(self):
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
        print("🛑 Simulator stopped")

def main():
    parser = argparse.ArgumentParser(description="Enterprise MQTT Simulator")
    parser.add_argument("--broker", required=True, help="MQTT broker URL")
    parser.add_argument("--duration", type=int, default=30, help="Normal simulation duration in seconds")
    parser.add_argument("--mode", choices=["normal", "anomaly", "both"], default="both", 
                       help="Simulation mode")
    
    args = parser.parse_args()
    
    simulator = EnterpriseSimulator(args.broker)
    
    if not simulator.connect():
        sys.exit(1)
    
    try:
        if args.mode in ["normal", "both"]:
            simulator.simulate_normal_operation(args.duration)
        
        if args.mode in ["anomaly", "both"]:
            simulator.simulate_anomalies()
            
    except KeyboardInterrupt:
        print("\n🛑 Simulation interrupted by user")
    finally:
        simulator.stop()

if __name__ == "__main__":
    main()