import paho.mqtt.client as mqtt
import requests
import json
import time
import logging
from typing import Dict, Any
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EnterpriseMQTTBridge")

class EnterpriseMQTTBridge:
    def __init__(self, mqtt_broker: str, ai_service_url: str):
        self.ai_service_url = ai_service_url
        self.stats = {
            "messages_received": 0,
            "predictions_made": 0,
            "anomalies_detected": 0,
            "start_time": time.time()
        }
        
        # FIXED: Use MQTTv311 instead of MQTTv5 to avoid deprecation warning
        self.client = mqtt.Client(client_id="enterprise_ai_bridge", protocol=mqtt.MQTTv311)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        # FIXED: Simple URL parsing
        if mqtt_broker.startswith("mqtts://"):
            self.use_tls = True
            broker_url = mqtt_broker.replace("mqtts://", "")
        elif mqtt_broker.startswith("mqtt://"):
            self.use_tls = False
            broker_url = mqtt_broker.replace("mqtt://", "")
        else:
            self.use_tls = False
            broker_url = mqtt_broker
        
        # Extract host and port
        if ":" in broker_url:
            self.broker_host, port_str = broker_url.split(":", 1)
            self.broker_port = int(port_str)
        else:
            self.broker_host = broker_url
            self.broker_port = 8883 if self.use_tls else 1883
        
        logger.info(f"🚀 Enterprise MQTT Bridge Initialized")
        logger.info(f"   MQTT Broker: {self.broker_host}:{self.broker_port}")
        logger.info(f"   AI Service: {self.ai_service_url}")
        logger.info(f"   TLS: {'Enabled' if self.use_tls else 'Disabled'}")
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("✅ Connected to MQTT Broker")
            # Subscribe to all sensor topics with explicit path segments
            client.subscribe("tenant/+/site/+/line/+/machine/+/sensor/+", qos=1)
            logger.info("📡 Subscribed to: tenant/+/site/+/line/+/machine/+/sensor/+")
            
            # Publish bridge status
            client.publish("enterprise/ai/bridge/status", json.dumps({
                "status": "online",
                "timestamp": time.time(),
                "version": "1.0.0"
            }), qos=1, retain=True)
        else:
            logger.error(f"❌ Failed to connect to MQTT broker, return code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        logger.warning(f"⚠️  Disconnected from MQTT broker (rc: {rc})")
    

def _on_message(self, client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        logger.info(f"📨 MQTT Message: {msg.topic} -> {payload}")

        # Safely schedule async processing from MQTT callback thread
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # Fallback if called before loop starts (should not happen in lifespan setup)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Schedule coroutine in the main event loop (assumed to exist in FastAPI app)
        asyncio.run_coroutine_threadsafe(self.process_mqtt_message(payload, msg.topic), loop)

    except Exception as e:
        logger.error(f"❌ MQTT message processing error: {e}")






























    
    def _process_sensor_data(self, payload: Dict[str, Any], topic: str):
        try:
            # Create unique nozzle ID from MQTT topic structure
            nozzle_id = f"{payload['tenant']}_{payload['site']}_{payload['line']}_{payload['machine']}_{payload['sensor']}"
            
            # Prepare data for AI service
            ai_payload = {
                "nozzle_id": nozzle_id,
                "timestamp": str(payload['timestamp']),
                "sensors": {
                    payload['sensor']: payload['value']
                }
            }
            
            # Call Enterprise AI Service
            start_time = time.time()
            response = requests.post(
                f"{self.ai_service_url}/predict",
                json=ai_payload,
                timeout=2.0
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                self.stats["predictions_made"] += 1
                
                # Log the prediction result
                status_emoji = "🔴" if result['status'] == 'ALARM' else "🟡" if result['status'] == 'WARN' else "🟢"
                logger.info(f"{status_emoji} {payload['sensor']}: {result['status']} "
                          f"(Score: {result.get('anomaly_score', 0):.3f}, "
                          f"Time: {response_time:.1f}ms)")
                
                # Publish anomaly alerts
                if result['status'] in ['WARN', 'ALARM']:
                    self.stats["anomalies_detected"] += 1
                    self._publish_anomaly_alert(payload, result, topic)
                
            else:
                logger.error(f"❌ AI Service error: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"⏰ AI Service timeout for {payload['sensor']}")
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Cannot connect to AI Service at {self.ai_service_url}")
        except Exception as e:
            logger.error(f"❌ Error calling AI Service: {e}")
    
    def _publish_anomaly_alert(self, original_payload: Dict, ai_result: Dict, original_topic: str):
        """Publish anomaly alerts to dedicated topic"""
        try:
            alert_topic = f"enterprise/anomalies/{original_payload['tenant']}/{original_payload['site']}"
            
            alert_payload = {
                "sensor": original_payload['sensor'],
                "value": original_payload['value'],
                "anomaly_score": ai_result.get('anomaly_score', 0),
                "status": ai_result['status'],
                "confidence": ai_result.get('confidence', 0),
                "severity": ai_result.get('severity', 'UNKNOWN'),
                "timestamp": original_payload['timestamp'],
                "recommendation": ai_result.get('recommendation', ''),
                "original_topic": original_topic,
                "ai_service_version": ai_result.get('model_version', '3.0.0')
            }
            
            self.client.publish(alert_topic, json.dumps(alert_payload), qos=1, retain=False)
            logger.info(f"🚨 Anomaly Alert Published: {original_payload['sensor']} - {ai_result['status']}")
            
        except Exception as e:
            logger.error(f"❌ Error publishing anomaly alert: {e}")
    
    def start(self):
        """Start the MQTT bridge"""
        try:
            logger.info("🚀 Starting Enterprise MQTT Bridge...")
            
            if self.use_tls:
                self.client.tls_set()
                
            self.client.connect(self.broker_host, self.broker_port, 60)
            
            # Start statistics thread
            stats_thread = threading.Thread(target=self._stats_reporter, daemon=True)
            stats_thread.start()
            
            logger.info("🏢 Enterprise MQTT Bridge is RUNNING")
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down Enterprise MQTT Bridge")
            self.client.disconnect()
        except Exception as e:
            logger.error(f"❌ Failed to start bridge: {e}")
    
    def _stats_reporter(self):
        """Periodically report bridge statistics"""
        while True:
            time.sleep(30)  # Report every 30 seconds
            uptime = time.time() - self.stats["start_time"]
            
            stats_msg = {
                "timestamp": time.time(),
                "uptime_seconds": uptime,
                "messages_received": self.stats["messages_received"],
                "predictions_made": self.stats["predictions_made"],
                "anomalies_detected": self.stats["anomalies_detected"],
                "messages_per_second": self.stats["messages_received"] / uptime if uptime > 0 else 0
            }
            
            self.client.publish("enterprise/ai/bridge/stats", json.dumps(stats_msg), qos=0, retain=False)
            logger.info(f"📊 Bridge Stats: {stats_msg['messages_received']} msgs, "
                       f"{stats_msg['predictions_made']} predictions, "
                       f"{stats_msg['anomalies_detected']} anomalies")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enterprise AI MQTT Bridge")
    parser.add_argument("--mqtt-broker", required=True, 
                       help="MQTT broker URL (mqtt://localhost:1883 or mqtts://host:8883)")
    parser.add_argument("--ai-service", default="http://localhost:8000",
                       help="AI service URL (default: http://localhost:8000)")
    
    args = parser.parse_args()
    
    bridge = EnterpriseMQTTBridge(
        mqtt_broker=args.mqtt_broker,
        ai_service_url=args.ai_service
    )
    
    bridge.start()