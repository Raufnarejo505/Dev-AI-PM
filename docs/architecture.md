# Architecture Overview

## Containers

| Service    | Tech                     | Responsibility                                           |
|------------|--------------------------|----------------------------------------------------------|
| `backend`  | FastAPI + SQLAlchemy     | REST APIs, MQTT ingestion, alarms, tickets, reports      |
| `ai-service` | FastAPI + IsolationForest | Stateful prediction service + rule fallback           |
| `postgres` | TimescaleDB              | Machines, sensors, hypertable `sensor_data`             |
| `mqtt`     | Eclipse Mosquitto        | Sensor ingestion bus                                     |
| `simulator`| Python + paho-mqtt       | Generates demo sensor traffic                            |
| `frontend` | React + Vite             | Modern dashboard UI                                      |
| `grafana`  | Grafana OSS              | Optional monitoring/observability                        |

## Data Flow

1. Sensor payload is published via MQTT (`simulator` or future edge gateway).
2. Backend MQTT worker inserts into Timescale `sensor_data`.
3. Threshold rules trigger alarms and auto-create tickets + notifications.
4. Backend optionally invokes AI service (`/predictions`) for advanced scoring.
5. Results stored in `predictions` table and exposed to frontend.
6. Frontend polls `/machines`, `/alarms`, `/tickets`, `/predictions` for visualisations.

## Backend Modules

- `app/api/routers`: FastAPI routers per resource.
- `app/services`: orchestration logic (alarms, predictions, reports, notifications).
- `app/mqtt/consumer.py`: background MQTT ingestion queue.
- `app/tasks/seed.py`: demo data population.
- `app/services/report_service.py`: CSV/PDF exports stored under `/app/reports`.

## Additional Features

- Auto ticket creation for alarms with severity >= warning.
- Notification dispatcher stub for SMTP + Slack.
- Report exports (CSV/PDF) with HTTP download.
- Knowledge base stub + ChatOps placeholder.
- Spare parts + RUL placeholder via AI service response.

