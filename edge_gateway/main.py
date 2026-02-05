#!/usr/bin/env python3
"""
OPC UA → MQTT Gateway Service

Industrial Edge Gateway that:
- Subscribes to OPC UA nodes using async subscriptions (not polling)
- Normalizes sensor data into standardized JSON payload
- Publishes to MQTT broker for downstream processing

Designed for production edge deployment.
"""

import asyncio
import json
import signal
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging

try:
    from asyncua import Client, ua
    from asyncua.common.subscription import Subscription
    from asyncua.common.events import Event
except ImportError:
    print("ERROR: asyncua library not installed. Install with: pip install asyncua")
    sys.exit(1)

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
logger = logging.getLogger("OPCUA_MQTT_Gateway")


class OPCUAMQTTGateway:
    """
    Gateway service that bridges OPC UA subscriptions to MQTT telemetry.
    
    Uses OPC UA subscriptions (not polling) for efficient real-time data collection.
    Handles reconnections gracefully and maintains subscription state.
    """
    
    def __init__(
        self,
        opcua_endpoint: str,
        mqtt_broker: str = "localhost",
        mqtt_port: int = 1883,
        machine_id: str = "extruder-01",
        sampling_interval_ms: int = 1000,
        namespace_index: int = 3
    ):
        self.opcua_endpoint = opcua_endpoint
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.machine_id = machine_id
        self.sampling_interval_ms = sampling_interval_ms
        self.namespace_index = namespace_index
        
        # OPC UA client and subscription
        self.opcua_client: Optional[Client] = None
        self.subscription: Optional[Subscription] = None
        self.subscription_handles: Dict[str, str] = {}  # node_id -> node_name mapping
        
        # MQTT client
        self.mqtt_client = mqtt.Client(
            client_id=f"opcua_gateway_{machine_id}",
            protocol=mqtt.MQTTv311
        )
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
        
        # State tracking
        self.running = False
        self._mqtt_connected = False
        self._publish_task: Optional[asyncio.Task] = None
        self._last_publish_monotonic: float = 0.0
        self._min_publish_interval_s: float = max(0.2, self.sampling_interval_ms / 1000.0)  # safety debounce
        self.reconnect_delay = 5
        self.stats = {
            "messages_published": 0,
            "opcua_errors": 0,
            "mqtt_errors": 0,
            "last_publish_time": None
        }
        
        # Current sensor values cache (for batching)
        self.sensor_cache: Dict[str, Any] = {
            "temperature": None,
            "vibration": None,
            "pressure": None,
            "motorCurrent": None,
            "wearIndex": None,
            "simulationProfile": None
        }
        
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback when MQTT client connects."""
        if rc == 0:
            self._mqtt_connected = True
            logger.info(f"Connected to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}")
        else:
            self._mqtt_connected = False
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
            self.stats["mqtt_errors"] += 1
    
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """Callback when MQTT client disconnects."""
        self._mqtt_connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection. Return code: {rc}")
    
    async def _connect_opcua(self) -> bool:
        """Establish connection to OPC UA server."""
        try:
            logger.info(f"Connecting to OPC UA server: {self.opcua_endpoint}")
            self.opcua_client = Client(url=self.opcua_endpoint, timeout=10)
            await self.opcua_client.connect()
            logger.info("Connected to OPC UA server")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to OPC UA server: {e}")
            self.stats["opcua_errors"] += 1
            return False
    
    async def _setup_subscriptions(self) -> bool:
        """Set up OPC UA subscriptions for all Extruder variables."""
        if not self.opcua_client:
            return False
        
        try:
            # Create subscription with desired sampling interval
            self.subscription = await self.opcua_client.create_subscription(
                period=self.sampling_interval_ms,
                handler=self
            )
            logger.info(f"Created OPC UA subscription (interval: {self.sampling_interval_ms}ms)")
            
            # Define node IDs for Extruder variables
            # Using namespace index 3 (Prosys Simulation Server default)
            nodes = {
                "temperature": f"ns={self.namespace_index};i=1009",
                "vibration": f"ns={self.namespace_index};i=1010",
                "pressure": f"ns={self.namespace_index};i=1011",
                "motorCurrent": f"ns={self.namespace_index};i=1012",
                "wearIndex": f"ns={self.namespace_index};i=1013",
                "simulationProfile": f"ns={self.namespace_index};i=1014"
            }
            
            # Subscribe to each node
            for name, node_id in nodes.items():
                try:
                    node = self.opcua_client.get_node(node_id)
                    # Subscribe with callback handler
                    handle = await self.subscription.subscribe_data_change(node)
                    # Store mapping: handle -> node_name for callback identification
                    self.subscription_handles[str(node.nodeid)] = name
                    logger.info(f"Subscribed to {name} ({node_id})")
                except Exception as e:
                    logger.error(f"Failed to subscribe to {name} ({node_id}): {e}")
                    self.stats["opcua_errors"] += 1
            
            if len(self.subscription_handles) > 0:
                logger.info(f"Successfully subscribed to {len(self.subscription_handles)} nodes")
                return True
            else:
                logger.error("No nodes subscribed successfully")
                return False
                
        except Exception as e:
            logger.error(f"Failed to set up OPC UA subscriptions: {e}")
            self.stats["opcua_errors"] += 1
            return False

    def datachange_notification(self, node, val, data):
        """asyncua subscription callback (required handler API)."""
        self._on_data_change(node, val, data)
    
    def _on_data_change(self, node, val, data):
        """
        Callback when OPC UA node value changes.
        
        This is called by the asyncua library whenever a subscribed node's
        value changes, based on the subscription's sampling interval.
        
        Args:
            node: The OPC UA node object
            val: The new value
            data: DataValue object with additional metadata
        """
        try:
            # Identify node by its node ID using our mapping
            node_id_str = str(node.nodeid)
            node_name = self.subscription_handles.get(node_id_str)
            
            # Fallback: identify by node ID pattern if mapping not found
            if not node_name:
                if "1009" in node_id_str:
                    node_name = "temperature"
                elif "1010" in node_id_str:
                    node_name = "vibration"
                elif "1011" in node_id_str:
                    node_name = "pressure"
                elif "1012" in node_id_str:
                    node_name = "motorCurrent"
                elif "1013" in node_id_str:
                    node_name = "wearIndex"
                elif "1014" in node_id_str:
                    node_name = "simulationProfile"
            
            if node_name:
                # Update cache
                old_value = self.sensor_cache.get(node_name)
                self.sensor_cache[node_name] = val
                
                if old_value != val:
                    logger.debug(f"{node_name}: {old_value} → {val}")
                
                # Publish normalized payload when we have all values
                if self._should_publish():
                    # Debounce publish scheduling: asyncua may deliver a burst of data changes
                    # (multiple monitored items / same tick). Only publish once per interval.
                    try:
                        loop = asyncio.get_event_loop()
                        if not loop.is_running():
                            loop.run_until_complete(self._publish_telemetry())
                            return

                        if self._publish_task is None or self._publish_task.done():
                            self._publish_task = asyncio.create_task(self._publish_telemetry())
                    except RuntimeError:
                        logger.warning("No event loop available for publishing")
            else:
                logger.warning(f"Received data change from unknown node: {node_id_str}")
                
        except Exception as e:
            logger.error(f"Error processing data change: {e}")
            self.stats["opcua_errors"] += 1
    
    def _should_publish(self) -> bool:
        """
        Determine if we should publish a telemetry message.
        
        Publishes when:
        - All sensor values are available, OR
        - Critical values (wearIndex) change
        """
        # Check if we have all required values
        required = ["temperature", "vibration", "pressure", "motorCurrent", "wearIndex"]
        has_all = all(self.sensor_cache.get(k) is not None for k in required)
        
        return has_all
    
    async def _publish_telemetry(self):
        """Publish normalized telemetry payload to MQTT."""
        try:
            now_mono = time.monotonic()
            if (now_mono - self._last_publish_monotonic) < self._min_publish_interval_s:
                return

            # Build normalized payload
            payload = self._normalize_payload()
            
            if not payload:
                return
            
            # Publish to MQTT (synchronous call, but we're in async context)
            topic = f"factory/{self.machine_id}/telemetry"
            message = json.dumps(payload)
            
            # MQTT publish is thread-safe, can be called from async context
            result = self.mqtt_client.publish(
                topic=topic,
                payload=message,
                qos=1,
                retain=False
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.stats["messages_published"] += 1
                self.stats["last_publish_time"] = datetime.now(timezone.utc).isoformat()
                self._last_publish_monotonic = now_mono
                logger.info(f"Published to {topic}: profile={payload.get('profile')}, temp={payload.get('temperature')}°C")
            else:
                logger.error(f"Failed to publish to MQTT. Return code: {result.rc}")
                self.stats["mqtt_errors"] += 1
                
        except Exception as e:
            logger.error(f"Error publishing telemetry: {e}")
            self.stats["mqtt_errors"] += 1
    
    def _normalize_payload(self) -> Optional[Dict[str, Any]]:
        """
        Normalize sensor data into standardized JSON payload format.
        
        Returns:
            Normalized payload dict or None if data is incomplete
        """
        # Check if we have all required values
        if any(self.sensor_cache.get(k) is None for k in
               ["temperature", "vibration", "pressure", "motorCurrent", "wearIndex"]):
            return None

        return {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "machineId": self.machine_id,
            "profile": int(self.sensor_cache["simulationProfile"]) if self.sensor_cache.get("simulationProfile") is not None else None,
            "temperature": float(self.sensor_cache["temperature"]),
            "vibration": float(self.sensor_cache["vibration"]),
            "pressure": float(self.sensor_cache["pressure"]),
            "motorCurrent": float(self.sensor_cache["motorCurrent"]),
            "wearIndex": float(self.sensor_cache["wearIndex"])
        }
    
    def _opcua_connected(self) -> bool:
        """Best-effort OPC UA connection check across asyncua versions."""
        if not self.opcua_client:
            return False

        checker = getattr(self.opcua_client, "is_connected", None)
        if callable(checker):
            try:
                return bool(checker())
            except Exception:
                # If the library check fails unexpectedly, don't crash the gateway loop.
                return True

        # Fallback: assume connected if we have a client and subscriptions are set up.
        return True
    
    async def _connect_mqtt(self) -> bool:
        """Connect to MQTT broker."""
        try:
            logger.info(f"Connecting to MQTT broker: {self.mqtt_broker}:{self.mqtt_port}")
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
            self.mqtt_client.loop_start()
            await asyncio.sleep(1)  # Give MQTT time to connect
            return self.mqtt_client.is_connected()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self.stats["mqtt_errors"] += 1
            return False
    
    async def _reconnect_opcua(self):
        """Handle OPC UA reconnection with exponential backoff."""
        while self.running:
            if await self._connect_opcua():
                if await self._setup_subscriptions():
                    self.reconnect_delay = 5  # Reset delay on success
                    return
            else:
                logger.warning(f"Retrying OPC UA connection in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, 60)  # Max 60s
    
    async def start(self):
        """Start the gateway service."""
        self.running = True
        logger.info("Starting OPC UA to MQTT Gateway")
        logger.info(f"OPCUA Endpoint: {self.opcua_endpoint}")
        logger.info(f"MQTT Broker: {self.mqtt_broker}:{self.mqtt_port}")
        logger.info(f"Machine ID: {self.machine_id}")
        logger.info(f"Sampling Interval: {self.sampling_interval_ms}ms")
        
        # Connect to MQTT first
        if not await self._connect_mqtt():
            logger.error("Failed to connect to MQTT broker. Exiting.")
            return
        
        # Connect to OPC UA and set up subscriptions
        await self._reconnect_opcua()
        
        # Main loop - keep service running
        try:
            while self.running:
                # Check OPC UA connection health
                if not self.opcua_client or not self.opcua_client.is_connected():
                    logger.warning("OPC UA connection lost. Reconnecting...")
                    await self._reconnect_opcua()
                
                # Check MQTT connection health
                if not self.mqtt_client.is_connected():
                    logger.warning("MQTT connection lost. Reconnecting...")
                    await self._connect_mqtt()
                
                # Log stats periodically
                await asyncio.sleep(30)
                logger.info(
                    f"Stats: Published={self.stats['messages_published']}, "
                    f"OPCUA Errors={self.stats['opcua_errors']}, "
                    f"MQTT Errors={self.stats['mqtt_errors']}"
                )
                
        except asyncio.CancelledError:
            logger.info("Gateway service cancelled")
        except Exception as e:
            logger.error(f"Fatal error in gateway loop: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the gateway service gracefully."""
        logger.info("Stopping OPC UA to MQTT Gateway...")
        self.running = False
        
        # Unsubscribe from OPC UA
        if self.subscription:
            try:
                await self.subscription.delete()
                logger.info("OPC UA subscription deleted")
            except Exception as e:
                logger.error(f"Error deleting subscription: {e}")
        
        # Disconnect OPC UA client
        if self.opcua_client:
            try:
                await self.opcua_client.disconnect()
                logger.info("OPC UA client disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting OPC UA client: {e}")
        
        # Disconnect MQTT client
        if self.mqtt_client:
            try:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                logger.info("MQTT client disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting MQTT client: {e}")
        
        logger.info("Gateway stopped")


async def main():
    """Main entry point."""
    import os
    
    # Configuration from environment variables
    opcua_endpoint = os.getenv("OPCUA_ENDPOINT", "opc.tcp://localhost:53530/OPCUA/SimulationServer")
    mqtt_broker = os.getenv("MQTT_BROKER", "localhost")
    mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
    machine_id = os.getenv("MACHINE_ID", "extruder-01")
    sampling_interval_ms = int(os.getenv("SAMPLING_INTERVAL_MS", "1000"))
    namespace_index = int(os.getenv("OPCUA_NAMESPACE_INDEX", "3"))
    
    # Create gateway instance
    gateway = OPCUAMQTTGateway(
        opcua_endpoint=opcua_endpoint,
        mqtt_broker=mqtt_broker,
        mqtt_port=mqtt_port,
        machine_id=machine_id,
        sampling_interval_ms=sampling_interval_ms,
        namespace_index=namespace_index
    )
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(gateway.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start gateway
    try:
        await gateway.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await gateway.stop()


if __name__ == "__main__":
    asyncio.run(main())
