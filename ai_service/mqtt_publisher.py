import paho.mqtt.client as mqtt
import json
import time
import random

def publish_test_sensor_data():
    client = mqtt.Client()
    
    try:
        client.connect("localhost", 1883, 60)
        print("✅ Connected to MQTT broker")
        
        sensors = ["pressure", "temperature", "motor_current", "vibration"]
        
        for i in range(20):
            test_message = {
                "tenant": "factory1",
                "site": "plantA", 
                "line": "line1",
                "machine": f"machine{i%3+1}",
                "sensor": random.choice(sensors),
                "value": random.uniform(100, 200),
                "timestamp": "2024-01-15T14:30:00Z"
            }
            
            # Use the exact topic structure your system expects
            topic = f"tenant/{test_message['tenant']}/site/{test_message['site']}/line/{test_message['line']}/machine/{test_message['machine']}/sensor/{test_message['sensor']}"
            
            client.publish(topic, json.dumps(test_message))
            print(f"📤 Message {i+1}: {test_message['sensor']} = {test_message['value']:.1f}")
            
            time.sleep(2)  # 2 second delay
            
        print("✅ All test messages sent!")
        
    except Exception as e:
        print(f"❌ MQTT connection failed: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    publish_test_sensor_data()