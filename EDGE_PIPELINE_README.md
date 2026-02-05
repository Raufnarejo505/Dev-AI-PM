# Industrial Edge Data Pipeline

## Overview

This is a production-ready industrial Edge data pipeline that demonstrates Industry 4.0 data flow patterns:

```
Prosys OPC UA Simulation Server
  → OPC UA → MQTT Gateway
  → MQTT Broker
  → Edge / AI Application
```

The pipeline consumes OPC UA sensor data from a simulated extruder machine, normalizes it, publishes it via MQTT, and processes it in an Edge/AI service exactly as it would be done in a real factory environment.

## Architecture

### Components

1. **OPC UA → MQTT Gateway** (`edge_gateway/`)
   - Subscribes to OPC UA nodes using async subscriptions (not polling)
   - Normalizes sensor data into standardized JSON payload
   - Publishes to MQTT broker with QoS 1
   - Handles reconnections gracefully

2. **Edge / AI Application** (`edge_ai/`)
   - Subscribes to MQTT telemetry topics
   - Validates message schema
   - Processes data based on simulation profile
   - Designed for pluggable AI model integration

3. **MQTT Broker** (Eclipse Mosquitto)
   - Central message broker
   - Topic format: `factory/{machineId}/telemetry`
   - QoS: 1 (at least once delivery)

### Machine Model (OPC UA)

The simulated extruder machine exposes the following nodes:

```
Extruder
 ├── Temperature (Float, °C)          - ns=3;i=1009
 ├── Vibration (Float, mm/s RMS)      - ns=3;i=1010
 ├── Pressure (Float, bar)             - ns=3;i=1011
 ├── MotorCurrent (Float, A)          - ns=3;i=1012
 ├── WearIndex (Float, %)              - ns=3;i=1013
 └── SimulationProfile (Int)           - ns=3;i=1014
     0 = Normal
     1 = EarlyWear
     2 = AdvancedWear
     3 = Fault
```

### Normalized MQTT Payload Format

```json
{
  "timestamp": "2026-01-08T09:15:32.421Z",
  "machineId": "extruder-01",
  "profile": 1,
  "temperature": 187.2,
  "vibration": 2.9,
  "pressure": 132.5,
  "motorCurrent": 14.1,
  "wearIndex": 18.4
}
```

## Prerequisites

1. **Prosys OPC UA Simulation Server**
   - Download and install from: https://www.prosysopc.com/products/opc-ua-simulation-server/
   - Default endpoint: `opc.tcp://localhost:53530/OPCUA/SimulationServer`
   - Ensure the server is running before starting the pipeline

2. **Docker and Docker Compose**
   - Docker Desktop or Docker Engine
   - Docker Compose v2+

3. **Python 3.11+** (for local development)

## Quick Start

### Option 1: Docker Compose (Recommended)

1. **Start the pipeline services:**

```bash
docker-compose up -d mqtt edge-gateway edge-ai
```

2. **Check logs:**

```bash
# Gateway logs
docker-compose logs -f edge-gateway

# Edge AI logs
docker-compose logs -f edge-ai
```

3. **Verify data flow:**

You should see:
- Gateway connecting to OPC UA server and subscribing to nodes
- Gateway publishing telemetry messages to MQTT
- Edge AI application receiving and processing messages
- Profile-based processing (Normal, EarlyWear, AdvancedWear, Fault)

### Option 2: Local Development

#### 1. Install Dependencies

```bash
# Gateway service
cd edge_gateway
pip install -r requirements.txt

# Edge AI service
cd ../edge_ai
pip install -r requirements.txt
```

#### 2. Start MQTT Broker

```bash
docker-compose up -d mqtt
```

#### 3. Configure Environment

**Gateway** (`edge_gateway/.env`):
```bash
OPCUA_ENDPOINT=opc.tcp://localhost:53530/OPCUA/SimulationServer
MQTT_BROKER=localhost
MQTT_PORT=1883
MACHINE_ID=extruder-01
SAMPLING_INTERVAL_MS=1000
OPCUA_NAMESPACE_INDEX=3
```

**Edge AI** (`edge_ai/.env`):
```bash
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_TOPIC_PATTERN=factory/+/telemetry
```

#### 4. Run Services

**Terminal 1 - Gateway:**
```bash
cd edge_gateway
python main.py
```

**Terminal 2 - Edge AI:**
```bash
cd edge_ai
python main.py
```

## Configuration

### Environment Variables

#### OPC UA → MQTT Gateway

| Variable | Default | Description |
|----------|---------|-------------|
| `OPCUA_ENDPOINT` | `opc.tcp://localhost:53530/OPCUA/SimulationServer` | OPC UA server endpoint URL |
| `MQTT_BROKER` | `localhost` | MQTT broker hostname |
| `MQTT_PORT` | `1883` | MQTT broker port |
| `MACHINE_ID` | `extruder-01` | Machine identifier for MQTT topic |
| `SAMPLING_INTERVAL_MS` | `1000` | OPC UA subscription sampling interval (ms) |
| `OPCUA_NAMESPACE_INDEX` | `3` | OPC UA namespace index for nodes |

#### Edge / AI Application

| Variable | Default | Description |
|----------|---------|-------------|
| `MQTT_BROKER` | `localhost` | MQTT broker hostname |
| `MQTT_PORT` | `1883` | MQTT broker port |
| `MQTT_TOPIC_PATTERN` | `factory/+/telemetry` | MQTT topic pattern to subscribe to |

### Docker Compose Configuration

For Docker deployments, the gateway uses `host.docker.internal` to access the OPC UA server running on the host machine. The `docker-compose.yml` already includes the necessary configuration for Linux compatibility.

**Alternative for Linux**: If `host.docker.internal` doesn't work, you can:
1. Use host network mode: `network_mode: "host"` (less secure)
2. Use the host's IP address directly
3. Run the gateway locally instead of in Docker

## Testing

### 1. Verify OPC UA Connection

Check gateway logs for successful connection:
```
✅ Connected to OPC UA server
📡 Created OPC UA subscription (interval: 1000ms)
  ✓ Subscribed to temperature (ns=3;i=1009)
  ✓ Subscribed to vibration (ns=3;i=1010)
  ...
```

### 2. Verify MQTT Publishing

Check gateway logs for published messages:
```
📤 Published to factory/extruder-01/telemetry: profile=0, temp=187.2°C
```

### 3. Verify Edge AI Processing

Check Edge AI logs for processed messages:
```
✅ NORMAL: Machine extruder-01 - Temp=187.2°C, Vib=2.9mm/s, ...
⚠️  EARLY WEAR: Machine extruder-01 - Wear Index=18.4% (threshold: 15-30%)
```

### 4. Monitor MQTT Messages

You can use an MQTT client to monitor messages:

```bash
# Using mosquitto_sub (if installed)
mosquitto_sub -h localhost -t "factory/+/telemetry" -v
```

## Simulation Profiles

The Prosys OPC UA Simulation Server can be configured to simulate different machine conditions:

- **Profile 0 (Normal)**: Normal operation, all values within acceptable ranges
- **Profile 1 (EarlyWear)**: Early wear condition, wear index 15-30%
- **Profile 2 (AdvancedWear)**: Advanced wear, wear index 30-50%
- **Profile 3 (Fault)**: Fault condition, system in error state

To change the profile in Prosys OPC UA Simulation Server:
1. Open the server configuration
2. Navigate to the SimulationProfile node
3. Change the value to 0, 1, 2, or 3
4. The gateway will detect the change and publish updated telemetry

## Architecture Details

### OPC UA Subscriptions vs Polling

This implementation uses **OPC UA subscriptions** (not polling) for efficient real-time data collection:

- **Subscriptions**: Server pushes data changes to client when values change
- **Polling**: Client repeatedly requests values (less efficient)

The gateway creates a subscription with a configurable sampling interval (default: 1 second) and receives callbacks when node values change.

### Data Normalization

The gateway normalizes all sensor data into a single JSON payload format:
- Timestamp in ISO-8601 UTC format
- Machine ID for routing
- Simulation profile for state awareness
- All sensor values in consistent format

### Profile-Based Processing

The Edge AI application routes telemetry to different processors based on the simulation profile:

- **Normal**: Logs data, ready for anomaly detection models
- **EarlyWear**: Warning logs, ready for predictive maintenance models
- **AdvancedWear**: Error logs, ready for failure prediction models
- **Fault**: Critical logs, ready for fault diagnosis models

### AI Model Integration

The `AIModelInterface` class provides a clean interface for integrating AI models:

```python
# In edge_ai/main.py
ai_models = AIModelInterface()
ai_models.load_model("anomaly_detection", "models/anomaly.pkl")
prediction = ai_models.predict("anomaly_detection", payload.to_dict())
```

This separation allows AI logic to be plugged in without modifying OPC UA/MQTT code.

## Production Deployment

### Security Considerations

1. **OPC UA Security**:
   - Use certificate-based authentication for production
   - Enable encryption (Sign & Encrypt)
   - Configure proper security policies

2. **MQTT Security**:
   - Use TLS/SSL for MQTT connections
   - Implement authentication (username/password or certificates)
   - Use ACLs to restrict topic access

3. **Network Security**:
   - Deploy gateway on edge device close to OPC UA server
   - Use VPN or secure network for MQTT communication
   - Implement firewall rules

### Monitoring and Logging

- Gateway logs connection status, subscription health, and publish statistics
- Edge AI logs message processing, validation errors, and profile-based events
- Use centralized logging (e.g., ELK stack, Splunk) for production

### Scaling

- Multiple gateways can connect to different OPC UA servers
- Edge AI applications can be scaled horizontally
- Use MQTT topic patterns to route messages to different processors

## Troubleshooting

### Gateway Cannot Connect to OPC UA Server

**Symptoms**: `❌ Failed to connect to OPC UA server`

**Solutions**:
1. Verify OPC UA server is running
2. Check endpoint URL is correct
3. Verify network connectivity
4. For Docker: Use `host.docker.internal` or host network mode

### No MQTT Messages Published

**Symptoms**: Gateway connects but no messages appear

**Solutions**:
1. Check OPC UA subscription status in logs
2. Verify node IDs are correct (ns=3;i=1009, etc.)
3. Check if OPC UA server has data in those nodes
4. Verify MQTT broker is accessible

### Edge AI Not Receiving Messages

**Symptoms**: Gateway publishes but Edge AI doesn't receive

**Solutions**:
1. Verify MQTT topic pattern matches: `factory/+/telemetry`
2. Check MQTT broker connectivity
3. Verify QoS settings (should be 1)
4. Check Edge AI subscription logs

### Invalid Payload Errors

**Symptoms**: `❌ Missing required field in payload`

**Solutions**:
1. Verify all OPC UA nodes are subscribed successfully
2. Check that all sensor values are being read
3. Verify payload normalization logic

## Development

### Project Structure

```
edge_gateway/
├── main.py              # OPC UA → MQTT Gateway service
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker image definition
└── env.example          # Environment variable template

edge_ai/
├── main.py              # Edge / AI Application
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker image definition
└── env.example          # Environment variable template
```

### Code Organization

- **Modular Design**: Clear separation between OPC UA, MQTT, and AI logic
- **Production Logging**: Structured logging with appropriate levels
- **Error Handling**: Graceful error handling with retry logic
- **Type Hints**: Full type annotations for maintainability

### Extending the Pipeline

1. **Add More Sensors**: Update node IDs in `edge_gateway/main.py`
2. **Add AI Models**: Implement model loading in `AIModelInterface`
3. **Add Data Storage**: Implement `_store_data()` in Edge AI application
4. **Add Alerting**: Integrate notification system in profile processors

## License

This is a demonstration project for industrial Edge data pipeline patterns.

## Support

For issues or questions:
1. Check logs for error messages
2. Verify configuration matches your environment
3. Ensure all prerequisites are installed and running
