import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

def test_mqtt_connection():
    """Test MQTT connection to public broker"""
    client = mqtt.Client(client_id=f"tester_{random.randint(1000, 9999)}")
    
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("✅ SUCCESS: Connected to public MQTT broker!")
            # Subscribe and publish a test message
            client.publish("test/connection", json.dumps({
                "message": "Hello from AI System",
                "timestamp": datetime.now().isoformat()
            }))
        else:
            print(f"❌ Failed to connect (rc: {rc})")
    
    def on_message(client, userdata, msg):
        print(f"📨 Received: {msg.topic} -> {msg.payload.decode()}")
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        print("🔗 Connecting to public MQTT broker (test.mosquitto.org)...")
        client.connect("test.mosquitto.org", 1883, 60)
        client.loop_start()
        
        # Wait for connection
        time.sleep(3)
        
        if client.is_connected():
            print("🎉 MQTT is working! Your system should connect now.")
            print("💡 Update your main.py to use: broker_host='test.mosquitto.org'")
        else:
            print("❌ Still not connected. Check your firewall/network.")
            
        time.sleep(2)
        client.loop_stop()
        
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    test_mqtt_connection()