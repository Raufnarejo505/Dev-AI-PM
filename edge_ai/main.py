#!/usr/bin/env python3
"""
Edge / AI Application

Industrial Edge application that:
- Subscribes to MQTT telemetry topics from OPC UA gateway
- Validates message schema
- Processes data based on simulation profile
- Logs data and prepares for AI model integration

Designed for production edge deployment with pluggable AI models.
"""

import json
import signal
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import logging

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("ERROR: paho-mqtt library not installed. Install with: pip install paho-mqtt")
    sys.exit(1)

# Configure production-style logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("EdgeAIApplication")


class TelemetryPayload:
    """Validated telemetry payload schema."""
    
    def __init__(self, data: Dict[str, Any]):
        self.timestamp = data["timestamp"]
        self.machine_id = data["machineId"]
        self.profile = int(data["profile"])
        self.temperature = float(data["temperature"])
        self.vibration = float(data["vibration"])
        self.pressure = float(data["pressure"])
        self.motor_current = float(data["motorCurrent"])
        self.wear_index = float(data["wearIndex"])
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional['TelemetryPayload']:
        """Create payload from dict with validation."""
        required_fields = [
            "timestamp", "machineId", "profile", "temperature",
            "vibration", "pressure", "motorCurrent", "wearIndex"
        ]
        
        for field in required_fields:
            if field not in data:
                logger.error(f"❌ Missing required field in payload: {field}")
                return None
        
        try:
            return cls(data)
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Invalid payload data type: {e}")
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "machineId": self.machine_id,
            "profile": self.profile,
            "temperature": self.temperature,
            "vibration": self.vibration,
            "pressure": self.pressure,
            "motorCurrent": self.motor_current,
            "wearIndex": self.wear_index
        }


class ProfileProcessor:
    """
    Process telemetry data based on simulation profile.
    
    Separates logic for different operational states:
    - Normal operation
    - Early wear detection
    - Advanced wear warning
    - Fault events
    """
    
    @staticmethod
    def process_normal(payload: TelemetryPayload):
        """Process data during normal operation (profile=0)."""
        logger.info(
            f"✅ NORMAL: Machine {payload.machine_id} - "
            f"Temp={payload.temperature:.1f}°C, "
            f"Vib={payload.vibration:.2f}mm/s, "
            f"Press={payload.pressure:.1f}bar, "
            f"Current={payload.motor_current:.1f}A, "
            f"Wear={payload.wear_index:.1f}%"
        )
        # TODO: Integrate AI model for normal operation monitoring
        # Example: anomaly_detection_model.predict(payload.to_dict())
    
    @staticmethod
    def process_early_wear(payload: TelemetryPayload):
        """Process data during early wear condition (profile=1)."""
        logger.warning(
            f"⚠️  EARLY WEAR: Machine {payload.machine_id} - "
            f"Wear Index={payload.wear_index:.1f}% (threshold: 15-30%)"
        )
        logger.warning(
            f"   Monitoring: Temp={payload.temperature:.1f}°C, "
            f"Vib={payload.vibration:.2f}mm/s, "
            f"Press={payload.pressure:.1f}bar"
        )
        # TODO: Integrate AI model for early wear prediction
        # Example: wear_prediction_model.predict(payload.to_dict())
        # Example: maintenance_scheduler.schedule_inspection(days=30)
    
    @staticmethod
    def process_advanced_wear(payload: TelemetryPayload):
        """Process data during advanced wear condition (profile=2)."""
        logger.error(
            f"ADVANCED WEAR: Machine {payload.machine_id} - "
            f"Wear Index={payload.wear_index:.1f}% (threshold: 30-50%)"
        )
        logger.error(
            f"   Critical: Temp={payload.temperature:.1f}°C, "
            f"Vib={payload.vibration:.2f}mm/s, "
            f"Press={payload.pressure:.1f}bar, "
            f"Current={payload.motor_current:.1f}A"
        )
        # TODO: Integrate AI model for advanced wear analysis
        # Example: failure_prediction_model.predict(payload.to_dict())
        # Example: alert_system.send_maintenance_alert()
        # Example: maintenance_scheduler.schedule_urgent_inspection(days=7)
    
    @staticmethod
    def process_fault(payload: TelemetryPayload):
        """Process data during fault condition (profile=3)."""
        logger.critical(
            f"FAULT: Machine {payload.machine_id} - "
            f"System in fault state!"
        )
        logger.critical(
            f"   Values: Temp={payload.temperature:.1f}°C, "
            f"Vib={payload.vibration:.2f}mm/s, "
            f"Press={payload.pressure:.1f}bar, "
            f"Current={payload.motor_current:.1f}A, "
            f"Wear={payload.wear_index:.1f}%"
        )
        # TODO: Integrate AI model for fault diagnosis
        # Example: fault_diagnosis_model.predict(payload.to_dict())
        # Example: alert_system.send_emergency_alert()
        # Example: maintenance_scheduler.schedule_immediate_shutdown()
    
    @classmethod
    def process(cls, payload: TelemetryPayload):
        """Route payload to appropriate processor based on profile."""
        profile = payload.profile
        
        if profile == 0:
            cls.process_normal(payload)
        elif profile == 1:
            cls.process_early_wear(payload)
        elif profile == 2:
            cls.process_advanced_wear(payload)
        elif profile == 3:
            cls.process_fault(payload)
        else:
            logger.warning(f"⚠️  Unknown profile value: {profile}. Treating as normal.")
            cls.process_normal(payload)


class AIModelInterface:
    """
    Interface for pluggable AI models.
    
    This class provides a clean interface for integrating AI models
    without mixing OPC UA/MQTT logic with AI logic.
    """
    
    def __init__(self):
        self.models = {}
        self.enabled = False  # Set to True when models are loaded
    
    def load_model(self, model_name: str, model_path: str):
        """Load an AI model from file or URL."""
        # TODO: Implement model loading
        # Example: self.models[model_name] = load_model(model_path)
        logger.info(f"AI Model '{model_name}' loaded from {model_path}")
        self.enabled = True
    
    def predict(self, model_name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run prediction using specified model."""
        if not self.enabled or model_name not in self.models:
            return None
        
        # TODO: Implement model prediction
        # Example: return self.models[model_name].predict(data)
        return None
    
    def is_available(self) -> bool:
        """Check if AI models are available."""
        return self.enabled


class EdgeAIApplication:
    """
    Main Edge/AI application that consumes MQTT telemetry.
    
    Subscribes to factory telemetry topics, validates messages,
    and processes them based on simulation profile.
    """
    
    def __init__(
        self,
        mqtt_broker: str = "localhost",
        mqtt_port: int = 1883,
        topic_pattern: str = "factory/+/telemetry"
    ):
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.topic_pattern = topic_pattern
        
        # MQTT client
        self.mqtt_client = mqtt.Client(
            client_id="edge_ai_app",
            protocol=mqtt.MQTTv311
        )
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message
        self.mqtt_client.on_disconnect = self._on_disconnect
        
        # AI model interface
        self.ai_models = AIModelInterface()
        
        # State tracking
        self.running = False
        self.stats = {
            "messages_received": 0,
            "messages_processed": 0,
            "messages_invalid": 0,
            "last_message_time": None
        }
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when MQTT client connects."""
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}")
            # Subscribe to telemetry topics
            client.subscribe(self.topic_pattern, qos=1)
            logger.info(f"Subscribed to topic pattern: {self.topic_pattern}")
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when MQTT client disconnects."""
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection. Return code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback when MQTT message is received."""
        try:
            self.stats["messages_received"] += 1
            self.stats["last_message_time"] = datetime.now().isoformat()
            
            # Parse JSON payload
            try:
                payload_dict = json.loads(msg.payload.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON in message: {e}")
                self.stats["messages_invalid"] += 1
                return
            
            # Validate and create payload object
            payload = TelemetryPayload.from_dict(payload_dict)
            if not payload:
                self.stats["messages_invalid"] += 1
                return
            
            # Process based on profile
            ProfileProcessor.process(payload)
            
            # Optional: Store data for later analysis
            # self._store_data(payload)
            
            self.stats["messages_processed"] += 1
            
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            self.stats["messages_invalid"] += 1
    
    def _store_data(self, payload: TelemetryPayload):
        """Store telemetry data (optional - for historical analysis)."""
        # TODO: Implement data storage
        # Example: Write to time-series database, file, or cloud storage
        pass
    
    def start(self):
        """Start the Edge/AI application."""
        self.running = True
        logger.info("Starting Edge/AI Application")
        logger.info(f"   MQTT Broker: {self.mqtt_broker}:{self.mqtt_port}")
        logger.info(f"   Topic Pattern: {self.topic_pattern}")
        logger.info(f"   AI Models: {'Enabled' if self.ai_models.is_available() else 'Disabled'}")
        
        try:
            # Connect to MQTT broker
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
            self.mqtt_client.loop_start()
            
            # Keep running
            import time
            while self.running:
                time.sleep(30)
                logger.info(
                    f"Stats: Received={self.stats['messages_received']}, "
                    f"Processed={self.stats['messages_processed']}, "
                    f"Invalid={self.stats['messages_invalid']}"
                )
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the Edge/AI application gracefully."""
        logger.info("Stopping Edge/AI Application...")
        self.running = False
        
        if self.mqtt_client:
            try:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                logger.info("MQTT client disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting MQTT client: {e}")
        
        logger.info("Application stopped")


def main():
    """Main entry point."""
    import os
    
    # Configuration from environment variables
    mqtt_broker = os.getenv("MQTT_BROKER", "localhost")
    mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
    topic_pattern = os.getenv("MQTT_TOPIC_PATTERN", "factory/+/telemetry")
    
    # Create application instance
    app = EdgeAIApplication(
        mqtt_broker=mqtt_broker,
        mqtt_port=mqtt_port,
        topic_pattern=topic_pattern
    )
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        app.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start application
    app.start()


if __name__ == "__main__":
    main()
