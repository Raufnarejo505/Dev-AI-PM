# Database Schema

## Machines
- `id` UUID (PK)
- `name`, `location`, `criticality`, `status`
- Relationships → sensors, sensor_data, alarms, tickets, predictions

## Sensors
- `id` UUID (PK)
- Foreign key to machine
- Threshold columns (`min`, `max`, `warning_threshold`, `critical_threshold`)

## Sensor Data (Timescale hypertable)
- `id` BIGSERIAL
- `sensor_id`, `machine_id`, `timestamp`, `value`, `status`
- Create hypertable after migration:
  ```sql
  SELECT create_hypertable('sensor_data', 'timestamp', if_not_exists => TRUE);
  ```

## Predictions
- Stores AI service responses with score, status, anomaly_type, metadata JSON.

## Alarms
- Links machine + sensor + optional prediction.
- Contains severity, status, message, triggered/resolved timestamps.

## Tickets
- Auto-created for alarms, includes priority, assignment, due date.

## Users
- Simple operator table for JWT auth scaffolding.

## Models
- Registry for uploaded model metadata (version, description).

