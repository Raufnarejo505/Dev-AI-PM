# Complete Service and Endpoint List

## 🌐 Access URLs

### Frontend (Web Interface)
- **URL**: http://37.120.176.43:3000
- **Port**: 3000 (mapped from container port 80)
- **Description**: Main web dashboard interface

### Backend API
- **Base URL**: http://37.120.176.43:3000/api
- **Direct Port**: 8000 (internal only, not exposed)
- **Description**: REST API for all backend operations

### AI Service
- **Base URL**: http://ai-service:8000 (internal only)
- **Port**: 8000 (internal only, accessed via backend)
- **Description**: AI anomaly detection service

### MQTT Broker
- **Host**: mqtt (internal) or 37.120.176.43
- **Port**: 1883
- **Description**: Message broker for sensor data

### Database (PostgreSQL/TimescaleDB)
- **Host**: postgres (internal) or localhost
- **Port**: 5432 (internal only, not exposed)
- **Database**: pm_db
- **User**: pm_user
- **Description**: Time-series database

## 📋 Backend API Endpoints

### Health & Status
- `GET /api/` - Root endpoint with service info
- `GET /api/health` - Basic health check
- `GET /api/health/live` - Liveness probe
- `GET /api/health/ready` - Readiness probe
- `GET /api/status` - Comprehensive system status

### Authentication
- `POST /api/users/register` - Register new user
- `POST /api/users/login` - Login
- `POST /api/users/refresh` - Refresh access token
- `POST /api/users/logout` - Logout
- `GET /api/users/me` - Get current user info
- `PUT /api/users/me` - Update current user
- `POST /api/users/forgot-password` - Request password reset
- `POST /api/users/reset-password` - Reset password

### Machines
- `GET /api/machines` - List all machines
- `POST /api/machines` - Create machine
- `GET /api/machines/{id}` - Get machine details
- `PUT /api/machines/{id}` - Update machine
- `DELETE /api/machines/{id}` - Delete machine
- `GET /api/machines/{id}/sensors` - Get machine sensors
- `GET /api/machines/{id}/stats` - Get machine statistics

### Sensors
- `GET /api/sensors` - List all sensors
- `POST /api/sensors` - Create sensor
- `GET /api/sensors/{id}` - Get sensor details
- `PUT /api/sensors/{id}` - Update sensor
- `DELETE /api/sensors/{id}` - Delete sensor
- `GET /api/sensors/{id}/data` - Get sensor data
- `GET /api/sensors/{id}/latest` - Get latest reading

### Sensor Data
- `GET /api/sensor-data` - Query sensor data
- `POST /api/sensor-data` - Ingest sensor data (MQTT)
- `GET /api/sensor-data/latest` - Get latest readings
- `GET /api/sensor-data/aggregate` - Get aggregated data

### Predictions
- `GET /api/predictions` - List predictions
- `POST /api/predictions/trigger` - Trigger prediction
- `GET /api/predictions/{id}` - Get prediction details
- `GET /api/predictions/latest` - Get latest predictions

### Alarms
- `GET /api/alarms` - List alarms
- `POST /api/alarms` - Create alarm
- `GET /api/alarms/{id}` - Get alarm details
- `PUT /api/alarms/{id}` - Update alarm
- `DELETE /api/alarms/{id}` - Delete alarm
- `POST /api/alarms/{id}/acknowledge` - Acknowledge alarm

### Tickets
- `GET /api/tickets` - List tickets
- `POST /api/tickets` - Create ticket
- `GET /api/tickets/{id}` - Get ticket details
- `PUT /api/tickets/{id}` - Update ticket
- `DELETE /api/tickets/{id}` - Delete ticket

### Dashboard
- `GET /api/dashboard/overview` - Dashboard overview stats
- `GET /api/dashboard/machines/stats` - Machine statistics
- `GET /api/dashboard/sensors/stats` - Sensor statistics
- `GET /api/dashboard/predictions/stats` - Prediction statistics

### Reports
- `POST /api/reports/generate` - Generate report
- `GET /api/reports` - List reports
- `GET /api/reports/{id}` - Get report details
- `GET /api/reports/{id}/download` - Download report
- `GET /api/reports/download/{filename}` - Download by filename

### AI Service (via Backend)
- `GET /api/ai/status` - AI service status
- `GET /api/ai/health` - AI service health
- `POST /api/ai/predict` - Trigger prediction
- `GET /api/ai/system/status` - Comprehensive AI status

### MQTT (via Backend)
- `GET /api/mqtt/status` - MQTT broker status
- `GET /api/mqtt/health` - MQTT health check

### Real-time
- `GET /api/realtime/events` - Server-Sent Events stream
- `WebSocket /api/ws` - WebSocket connection

### Settings
- `GET /api/settings` - Get settings
- `PUT /api/settings` - Update settings

### Notifications
- `GET /api/notifications/status` - Notification status
- `POST /api/notifications/test-email` - Test email
- `POST /api/notifications/test-webhook` - Test webhook

### Webhooks
- `GET /api/webhooks` - List webhooks
- `POST /api/webhooks` - Create webhook
- `PUT /api/webhooks/{id}` - Update webhook
- `DELETE /api/webhooks/{id}` - Delete webhook

### Roles
- `GET /api/roles` - List roles
- `POST /api/roles` - Create role
- `GET /api/roles/{id}` - Get role details

### API Documentation
- `GET /api/docs` - Swagger UI documentation
- `GET /api/openapi.json` - OpenAPI specification
- `GET /api/redoc` - ReDoc documentation

## 🤖 AI Service Endpoints (Internal)

Access via backend proxy: `/api/ai/*` or directly at `http://ai-service:8000` (internal)

- `GET /health` - Health check
- `GET /system/status` - System status
- `POST /predict` - Trigger prediction
- `GET /metrics` - Performance metrics

## 📡 MQTT Topics

The simulator publishes to:
- `factory/demo/line1/machine1/sensors` - Pump-01 sensors
- `factory/demo/line2/machine2/sensors` - Motor-02 sensors
- `factory/demo/line3/machine3/sensors` - Compressor-A sensors
- `factory/demo/line2/conveyor/sensors` - Conveyor-B2 sensors

Backend subscribes to:
- `factory/#` - All factory topics
- `edge/#` - Edge device topics

## 🔧 Service Ports Summary

| Service | External Port | Internal Port | Access Method |
|---------|--------------|--------------|---------------|
| Frontend | 3000 | 80 | http://37.120.176.43:3000 |
| Backend API | - | 8000 | http://37.120.176.43:3000/api |
| AI Service | - | 8000 | Via backend only |
| MQTT | 1883 | 1883 | mqtt://37.120.176.43:1883 |
| Database | - | 5432 | Internal only |

## 🚀 Quick Access Commands

```bash
# Frontend
curl http://37.120.176.43:3000

# Backend Health
curl http://37.120.176.43:3000/api/health

# Backend Status
curl http://37.120.176.43:3000/api/status

# AI Status (via backend)
curl http://37.120.176.43:3000/api/ai/status

# MQTT Status (via backend)
curl http://37.120.176.43:3000/api/mqtt/status

# API Documentation
# Open in browser: http://37.120.176.43:3000/api/docs
```

## 📝 Notes

- All API endpoints require authentication except `/health`, `/health/live`, and `/status`
- Use JWT token in `Authorization: Bearer <token>` header
- Frontend automatically handles authentication
- Internal services (AI, Database) are not directly accessible from outside
- MQTT port 1883 is exposed for external sensor devices



