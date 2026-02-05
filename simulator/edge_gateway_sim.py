"""
Edge gateway simulator that batches readings during offline windows
and publishes them when connectivity resumes.
"""

import json
import os
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
TOPIC = "edge/aggregated"


def main():
    buffer = []
    online = True
    client = mqtt.Client()

    while True:
        # Simulate intermittent connectivity
        online = random.random() > 0.2

        reading = {
            "sensor_id": "edge-temp",
            "machine_id": "edge-gateway",
            "value": round(random.uniform(60, 120), 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        buffer.append(reading)

        if online and buffer:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            client.loop_start()
            payload = {"batch": buffer[:]}
            client.publish(TOPIC, json.dumps(payload))
            client.loop_stop()
            buffer.clear()

        time.sleep(2)


if __name__ == "__main__":
    main()

