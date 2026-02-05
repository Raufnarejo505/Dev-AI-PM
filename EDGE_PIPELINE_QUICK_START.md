# Edge Pipeline Quick Start Guide

## 🚀 Quick Start (5 minutes)

### Prerequisites
1. **Prosys OPC UA Simulation Server** running on `localhost:53530`
2. **Docker and Docker Compose** installed

### Start the Pipeline

```bash
# Start MQTT broker and Edge services
docker-compose up -d mqtt edge-gateway edge-ai

# Watch the logs
docker-compose logs -f edge-gateway edge-ai
```

### What You Should See

**Gateway logs:**
```
✅ Connected to OPC UA server
📡 Created OPC UA subscription (interval: 1000ms)
  ✓ Subscribed to temperature (ns=3;i=1009)
  ✓ Subscribed to vibration (ns=3;i=1010)
  ...
📤 Published to factory/extruder-01/telemetry: profile=0, temp=187.2°C
```

**Edge AI logs:**
```
✅ Connected to MQTT broker
📡 Subscribed to topic pattern: factory/+/telemetry
✅ NORMAL: Machine extruder-01 - Temp=187.2°C, Vib=2.9mm/s, ...
```

## 📋 Local Development

### 1. Install Dependencies

```bash
# Gateway
cd edge_gateway
pip install -r requirements.txt

# Edge AI
cd ../edge_ai
pip install -r requirements.txt
```

### 2. Start MQTT Broker

```bash
docker-compose up -d mqtt
```

### 3. Configure Environment

Create `edge_gateway/.env`:
```bash
OPCUA_ENDPOINT=opc.tcp://localhost:53530/OPCUA/SimulationServer
MQTT_BROKER=localhost
MQTT_PORT=1883
MACHINE_ID=extruder-01
SAMPLING_INTERVAL_MS=1000
OPCUA_NAMESPACE_INDEX=3
```

Create `edge_ai/.env`:
```bash
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_TOPIC_PATTERN=factory/+/telemetry
```

### 4. Run Services

**Terminal 1:**
```bash
cd edge_gateway
python main.py
```

**Terminal 2:**
```bash
cd edge_ai
python main.py
```

## 🔍 Verify Data Flow

### Monitor MQTT Messages

```bash
# Install mosquitto clients (if not installed)
# macOS: brew install mosquitto
# Ubuntu: sudo apt-get install mosquitto-clients

# Subscribe to telemetry topics
mosquitto_sub -h localhost -t "factory/+/telemetry" -v
```

### Check Service Status

```bash
# Gateway status
docker-compose ps edge-gateway

# Edge AI status
docker-compose ps edge-ai

# View logs
docker-compose logs --tail=50 edge-gateway
docker-compose logs --tail=50 edge-ai
```

## 🎯 Test Different Profiles

In Prosys OPC UA Simulation Server:

1. Open the server
2. Navigate to node `ns=3;i=1014` (SimulationProfile)
3. Change value to:
   - `0` = Normal operation
   - `1` = Early wear
   - `2` = Advanced wear
   - `3` = Fault

Watch the Edge AI logs change:
- Profile 0: `✅ NORMAL: ...`
- Profile 1: `⚠️  EARLY WEAR: ...`
- Profile 2: `🔴 ADVANCED WEAR: ...`
- Profile 3: `🚨 FAULT: ...`

## 🛠️ Troubleshooting

### Gateway Can't Connect to OPC UA

**Check:**
- Is Prosys OPC UA Simulation Server running?
- Is the endpoint URL correct?
- For Docker: Use `host.docker.internal` or host IP

**Fix:**
```bash
# Check OPC UA server
# Windows: Check if service is running
# Linux/Mac: Check if port 53530 is listening
netstat -an | grep 53530
```

### No MQTT Messages

**Check:**
- Is MQTT broker running? `docker-compose ps mqtt`
- Are subscriptions successful? Check gateway logs
- Are node IDs correct? (ns=3;i=1009, etc.)

### Edge AI Not Receiving

**Check:**
- Is topic pattern correct? `factory/+/telemetry`
- Is MQTT broker accessible?
- Check Edge AI subscription logs

## 📁 Project Structure

```
edge_gateway/
├── main.py              # OPC UA → MQTT Gateway
├── requirements.txt     # asyncua, paho-mqtt
├── Dockerfile
├── env.example
└── start.sh

edge_ai/
├── main.py              # Edge / AI Application
├── requirements.txt     # paho-mqtt
├── Dockerfile
├── env.example
└── start.sh
```

## 🔗 Next Steps

1. **Integrate AI Models**: See `AIModelInterface` in `edge_ai/main.py`
2. **Add Data Storage**: Implement `_store_data()` method
3. **Add Alerting**: Integrate notification system
4. **Scale**: Deploy multiple gateways for multiple machines

## 📚 Full Documentation

See `EDGE_PIPELINE_README.md` for complete documentation.
