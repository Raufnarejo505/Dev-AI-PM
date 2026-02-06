import json
import os
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

# Local MQTT broker configuration
LOCAL_MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
LOCAL_MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))

# Cloud MQTT broker configuration (your real sensor data source)
CLOUD_MQTT_URL = os.getenv("MQTT_CLOUD_URL", "")
CLOUD_MQTT_USERNAME = os.getenv("MQTT_CLOUD_USERNAME", "")
CLOUD_MQTT_PASSWORD = os.getenv("MQTT_CLOUD_PASSWORD", "")
CLOUD_MQTT_PORT = int(os.getenv("MQTT_CLOUD_PORT", "1883"))

# Topic mapping from cloud to local
# Map your cloud topics to local topics that the backend expects
CLOUD_TO_LOCAL_TOPICS = {
    # Add your cloud topic mappings here
    # Example: "factory/line1/machine1/temperature": "factory/demo/line1/machine1/sensors",
    # Example: "sensors/extruder/pressure": "factory/demo/line1/machine1/sensors",
    # Default topic if no mapping found
    "default": "factory/demo/line1/machine1/sensors"
}

def main():
    print(f"🌐 Real Sensor Data Bridge - Cloud to Local MQTT")
    print(f"📍 Local MQTT: {LOCAL_MQTT_HOST}:{LOCAL_MQTT_PORT}")
    print(f"☁️  Cloud MQTT: {CLOUD_MQTT_URL}:{CLOUD_MQTT_PORT}")
    
    if not CLOUD_MQTT_URL:
        print("❌ ERROR: MQTT_CLOUD_URL environment variable not set!")
        print("   Please set your cloud MQTT broker URL in .env file")
        print("   Example: MQTT_CLOUD_URL=mqtt://your-cloud-broker.com")
        return
    
    # Create clients for both cloud and local MQTT
    cloud_client = mqtt.Client(client_id="cloud-bridge")
    local_client = mqtt.Client(client_id="local-bridge")
    
    # Configure cloud client authentication
    if CLOUD_MQTT_USERNAME and CLOUD_MQTT_PASSWORD:
        cloud_client.username_pw_set(CLOUD_MQTT_USERNAME, CLOUD_MQTT_PASSWORD)
    
    # Connection callbacks
    def on_cloud_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Connected to cloud MQTT broker")
            # Subscribe to all sensor topics from cloud
            client.subscribe("sensors/+", qos=1)
            client.subscribe("factory/+/+", qos=1)
            client.subscribe("machines/+/sensors", qos=1)
            print(f"📡 Subscribed to cloud sensor topics")
        else:
            print(f"❌ Cloud MQTT connection failed with return code {rc}")
    
    def on_local_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Connected to local MQTT broker")
        else:
            print(f"❌ Local MQTT connection failed with return code {rc}")
    
    def on_cloud_message(client, userdata, msg):
        """Receive message from cloud and forward to local MQTT"""
        try:
            # Parse the cloud message
            payload = json.loads(msg.payload.decode())
            topic = msg.topic
            
            print(f"📨 Received from cloud: {topic}")
            
            # Map cloud topic to local topic
            local_topic = CLOUD_TO_LOCAL_TOPICS.get(topic, CLOUD_TO_LOCAL_TOPICS["default"])
            
            # Transform payload to match expected format
            transformed_payload = {
                "sensor_id": payload.get("sensor_id", "unknown"),
                "machine_id": payload.get("machine_id", "machine-1"),
                "metric": payload.get("metric", payload.get("name", "value")),
                "value": float(payload.get("value", 0)),
                "unit": payload.get("unit", ""),
                "timestamp": payload.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "location": payload.get("location", ""),
                "status": payload.get("status", "normal"),
                "metadata": {
                    "source": "cloud_bridge",
                    "original_topic": topic,
                    "cloud_timestamp": payload.get("timestamp"),
                    "machine_name": payload.get("machine_name", ""),
                }
            }
            
            # Forward to local MQTT
            local_client.publish(local_topic, json.dumps(transformed_payload))
            print(f"📤 Forwarded to local: {local_topic} -> {transformed_payload['metric']}={transformed_payload['value']}")
            
        except Exception as e:
            print(f"❌ Error processing cloud message: {e}")
            print(f"   Topic: {msg.topic}")
            print(f"   Payload: {msg.payload}")
    
    def on_cloud_disconnect(client, userdata, rc):
        if rc != 0:
            print(f"⚠️ Cloud MQTT disconnected unexpectedly (rc: {rc})")
    
    def on_local_disconnect(client, userdata, rc):
        if rc != 0:
            print(f"⚠️ Local MQTT disconnected unexpectedly (rc: {rc})")
    
    # Set callbacks
    cloud_client.on_connect = on_cloud_connect
    cloud_client.on_message = on_cloud_message
    cloud_client.on_disconnect = on_cloud_disconnect
    
    local_client.on_connect = on_local_connect
    local_client.on_disconnect = on_local_disconnect
    
    # Connect to both brokers
    print(f"🔄 Connecting to cloud MQTT broker...")
    try:
        cloud_client.connect(CLOUD_MQTT_URL, CLOUD_MQTT_PORT, keepalive=60)
        cloud_client.loop_start()
        time.sleep(2)
    except Exception as e:
        print(f"❌ Failed to connect to cloud MQTT: {e}")
        return
    
    print(f"🔄 Connecting to local MQTT broker...")
    try:
        local_client.connect(LOCAL_MQTT_HOST, LOCAL_MQTT_PORT, keepalive=60)
        local_client.loop_start()
        time.sleep(2)
    except Exception as e:
        print(f"❌ Failed to connect to local MQTT: {e}")
        return
    
    # Verify connections
    if not cloud_client.is_connected():
        print("❌ Cloud MQTT connection failed")
        return
    
    if not local_client.is_connected():
        print("❌ Local MQTT connection failed")
        return
    
    print(f"✅ Real sensor data bridge is active!")
    print(f"🔄 Forwarding real sensor data from cloud to local MQTT")
    print(f"📊 Waiting for real sensor data...")
    
    try:
        # Keep the bridge running
        while True:
            time.sleep(10)
            
            # Verify connections are still active
            if not cloud_client.is_connected():
                print("⚠️ Cloud MQTT connection lost, attempting to reconnect...")
                try:
                    cloud_client.reconnect()
                except:
                    pass
            
            if not local_client.is_connected():
                print("⚠️ Local MQTT connection lost, attempting to reconnect...")
                try:
                    local_client.reconnect()
                except:
                    pass
                
    except KeyboardInterrupt:
        print("\n🛑 Real sensor data bridge stopped by user")
    except Exception as e:
        print(f"❌ Error in bridge: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if cloud_client.is_connected():
            cloud_client.loop_stop()
            cloud_client.disconnect()
        if local_client.is_connected():
            local_client.loop_stop()
            local_client.disconnect()
        print("🔚 Bridge shutdown complete")


if __name__ == "__main__":
    main()
