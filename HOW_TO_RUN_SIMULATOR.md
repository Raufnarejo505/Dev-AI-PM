# How to Run the Simulator

The simulator generates realistic sensor data and publishes it to MQTT for testing the system.

## Option 1: Enable Simulator in Production (Recommended for Testing)

### Step 1: Edit docker-compose.prod.yml

Uncomment the simulator section:

```bash
nano docker-compose.prod.yml
```

Find this section (around line 107) and uncomment it:

```yaml
  simulator:
    build:
      context: ./simulator
      dockerfile: Dockerfile
    restart: unless-stopped
    depends_on:
      - mqtt
    environment:
      MQTT_BROKER_HOST: mqtt
      MQTT_BROKER_PORT: 1883
    networks:
      - pm-net
```

### Step 2: Start the simulator

```bash
docker compose -f docker-compose.prod.yml up -d simulator
```

### Step 3: Check simulator logs

```bash
docker compose -f docker-compose.prod.yml logs simulator -f
```

You should see:
- ✅ Connected to MQTT broker
- 📊 Simulating X machines with Y sensors
- 📈 Cycle updates

## Option 2: Run Simulator Manually (Without Docker)

### Step 1: Connect to backend container

```bash
docker compose -f docker-compose.prod.yml exec backend bash
```

### Step 2: Install dependencies (if needed)

```bash
pip install paho-mqtt
```

### Step 3: Run simulator script

```bash
cd /path/to/simulator
python publish_sim.py
```

Or from project root:

```bash
python simulator/publish_sim.py
```

## Option 3: Run Simulator as Standalone Container

### Step 1: Build simulator image

```bash
docker compose -f docker-compose.prod.yml build simulator
```

### Step 2: Run simulator container

```bash
docker compose -f docker-compose.prod.yml run --rm simulator
```

## What the Simulator Does

The simulator:
- ✅ Publishes sensor data to MQTT topics: `factory/demo/line*/machine*/sensors`
- ✅ Simulates 4 machines with multiple sensors each
- ✅ Generates realistic values with occasional anomalies
- ✅ Creates warning and critical states
- ✅ Updates every 0.5 seconds

## Simulated Machines

1. **Pump-01** (Building A, Floor 2)
   - Pressure, Temperature, Vibration, Flow sensors

2. **Motor-02** (Building B, Floor 1)
   - Current, Temperature, Vibration, RPM sensors

3. **Compressor-A** (Building C, Floor 3)
   - Pressure, Temperature, Oil Level, Vibration sensors

4. **Conveyor-B2** (Building B, Floor 2)
   - Speed, Load, Temperature, Torque sensors

## Verify Simulator is Working

### Check MQTT messages

```bash
# Install mosquitto clients (if not installed)
apt install mosquitto-clients -y

# Subscribe to MQTT topics
docker compose -f docker-compose.prod.yml exec mqtt mosquitto_sub -h localhost -t "factory/#" -v
```

You should see JSON messages with sensor data.

### Check backend is receiving data

```bash
# Check backend logs for MQTT ingestion
docker compose -f docker-compose.prod.yml logs backend | grep -i mqtt

# Check sensor data in database
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "SELECT COUNT(*) FROM sensor_data;"
```

### Check dashboard

After simulator runs for a few minutes:
- Go to http://37.120.176.43:3000
- Check Dashboard - should show live sensor data
- Check Predictions - should show AI predictions
- Check Sensors page - should show sensor readings

## Stop Simulator

```bash
# Stop simulator container
docker compose -f docker-compose.prod.yml stop simulator

# Or remove it
docker compose -f docker-compose.prod.yml rm -f simulator
```

## Troubleshooting

### Simulator can't connect to MQTT

```bash
# Check MQTT is running
docker compose -f docker-compose.prod.yml ps mqtt

# Check MQTT logs
docker compose -f docker-compose.prod.yml logs mqtt

# Test MQTT connection
docker compose -f docker-compose.prod.yml exec simulator python -c "import paho.mqtt.client as mqtt; c = mqtt.Client(); c.connect('mqtt', 1883); print('Connected!')"
```

### No data appearing in dashboard

1. Wait 1-2 minutes for data to accumulate
2. Check backend is ingesting MQTT messages
3. Check AI service is processing data
4. Refresh dashboard

## Quick Start Commands

```bash
# Enable and start simulator
docker compose -f docker-compose.prod.yml up -d simulator

# View logs
docker compose -f docker-compose.prod.yml logs simulator -f

# Stop simulator
docker compose -f docker-compose.prod.yml stop simulator
```

---

**Note**: The simulator is disabled in production by default. Enable it only for testing/demo purposes.

