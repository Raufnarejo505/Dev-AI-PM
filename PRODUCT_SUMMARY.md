# Predictive Maintenance Platform - Complete Product Summary

## 📋 Table of Contents

1. [Product Overview](#product-overview)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [Features & Capabilities](#features--capabilities)
5. [Data Flow & Working Process](#data-flow--working-process)
6. [Installation & Setup](#installation--setup)
7. [Running the System](#running-the-system)
8. [Testing Guide](#testing-guide)
9. [API Documentation](#api-documentation)
10. [Configuration](#configuration)
11. [Troubleshooting](#troubleshooting)

---

## Product Overview

The **Predictive Maintenance Platform** is a comprehensive Industrial IoT (IIoT) solution designed for real-time monitoring, anomaly detection, and predictive maintenance of industrial machinery. The platform combines sensor data ingestion, AI-powered analytics, and a modern web interface to enable proactive maintenance strategies.

### Key Value Propositions

- **Real-time Monitoring**: Live sensor data ingestion via MQTT
- **AI-Powered Predictions**: Isolation Forest anomaly detection with rule-based fallback
- **Automated Alerts**: Automatic alarm and ticket generation
- **Modern Dashboard**: Real-time visualization and analytics
- **Scalable Architecture**: Microservices-based design with Docker
- **Enterprise Ready**: RBAC, audit logging, webhooks, and reporting

---

## System Architecture

### High-Level Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│  Database  │
│  (React)    │◀────│  (FastAPI)  │◀────│ (Timescale)│
└─────────────┘     └─────────────┘     └─────────────┘
                            │
                            ├────▶ AI Service (FastAPI)
                            │
                            ├────▶ MQTT Broker (Mosquitto)
                            │
                            └────▶ Simulator (Data Generator)
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | React 18 + TypeScript + Vite | Modern web dashboard |
| **Backend** | FastAPI + Python 3.11 | REST API and business logic |
| **Database** | TimescaleDB (PostgreSQL 15) | Time-series data storage |
| **AI Service** | FastAPI + scikit-learn | Anomaly detection |
| **MQTT Broker** | Eclipse Mosquitto | Sensor data ingestion |
| **Containerization** | Docker + Docker Compose | Service orchestration |

---

## Core Components

### 1. Backend Service (Port 8000)

**Technology**: FastAPI, async SQLAlchemy, Alembic

**Responsibilities**:
- RESTful API endpoints
- MQTT message consumption
- Database operations
- Authentication & authorization
- Business logic orchestration
- Report generation

**Key Modules**:
- `app/api/routers/` - API endpoint definitions (25+ routers)
- `app/services/` - Business logic layer
- `app/models/` - Database models (SQLAlchemy)
- `app/schemas/` - Request/response schemas (Pydantic)
- `app/mqtt/consumer.py` - MQTT message processor
- `app/core/` - Configuration and security

### 2. Frontend Service (Port 3000)

**Technology**: React 18, TypeScript, Tailwind CSS, React Query

**Responsibilities**:
- User interface and dashboard
- Real-time data visualization
- User authentication
- Data management (CRUD operations)
- Report generation and download

**Key Features**:
- Responsive design with dark theme
- Real-time updates (10-second refresh)
- Role-based UI rendering
- Error handling and offline support
- PDF/CSV report downloads

### 3. AI Service (Port 8001)

**Technology**: FastAPI, scikit-learn, Isolation Forest

**Responsibilities**:
- Anomaly detection on sensor data
- Feature engineering (25 features)
- Model inference
- Rule-based fallback system
- Performance metrics tracking

**Model Details**:
- **Algorithm**: Isolation Forest
- **Features**: 25 statistical and temporal features
- **Fallback**: Rule-based threshold system
- **Output**: Anomaly score, confidence, prediction class

### 4. Database (Port 5432)

**Technology**: TimescaleDB (PostgreSQL 15 extension)

**Responsibilities**:
- Time-series data storage (sensor_data hypertable)
- Relational data (machines, sensors, users, etc.)
- Data persistence and querying
- Database migrations (Alembic)

**Key Tables**:
- `sensor_data` - Time-series sensor readings (hypertable)
- `machine` - Machine definitions
- `sensor` - Sensor definitions
- `prediction` - AI predictions
- `alarm` - Generated alarms
- `ticket` - Maintenance tickets
- `user` - User accounts
- `auditlog` - Audit trail
- `settings` - System configuration
- `webhook` - Webhook configurations

### 5. MQTT Broker (Port 1883)

**Technology**: Eclipse Mosquitto

**Responsibilities**:
- Message broker for sensor data
- Topic-based message routing
- Message persistence (optional)

**Topics**:
- `factory/#` - Factory sensor data
- `edge/#` - Edge gateway data
- `sensors/+/telemetry` - Generic sensor telemetry

### 6. Simulator (Background Service)

**Technology**: Python + paho-mqtt

**Responsibilities**:
- Generate realistic sensor data
- Publish to MQTT topics
- Simulate multiple machines and sensors

**Simulated Data**:
- Temperature, pressure, vibration
- Motor current, RPM, flow rate
- Oil level, belt speed, load weight

---

## Features & Capabilities

### 1. Authentication & Authorization

**JWT-Based Authentication**:
- Access tokens (60-minute expiry)
- Refresh tokens (30-day expiry)
- Secure password hashing (bcrypt)

**Role-Based Access Control (RBAC)**:
- **Admin**: Full system access
- **Engineer**: Machine/sensor management, predictions
- **Viewer**: Read-only access to dashboards and reports

**Demo Users**:
- `admin@example.com` / `admin123` (Admin)
- `engineer@example.com` / `engineer123` (Engineer)
- `viewer@example.com` / `viewer123` (Viewer)

### 2. Real-Time Data Ingestion

**MQTT Integration**:
- Automatic machine and sensor registration
- Support for multiple sensor values per message
- Queue-based processing for reliability
- Automatic threshold checking

**Data Processing**:
- Real-time sensor data ingestion
- Automatic status calculation (normal/warning/critical)
- Threshold-based alarm generation
- AI prediction triggering

### 3. AI-Powered Anomaly Detection

**Isolation Forest Model**:
- Unsupervised anomaly detection
- 25-feature engineering pipeline
- Statistical and temporal feature extraction
- Confidence scoring

**Rule-Based Fallback**:
- Threshold-based detection
- Configurable warning/critical levels
- Machine-specific thresholds

**Prediction Output**:
- Anomaly score (0.0-1.0)
- Confidence level
- Prediction class (normal/warning/critical)
- Recommended action
- Remaining Useful Life (RUL) estimation

### 4. Alarm Management

**Automatic Alarm Generation**:
- Threshold violations
- AI prediction anomalies
- Machine status changes

**Alarm Features**:
- Severity levels (info, warning, critical)
- Status tracking (active, resolved, acknowledged)
- Comments and attachments
- Automatic ticket creation
- Email notifications (optional)

### 5. Ticket System

**Maintenance Tickets**:
- Auto-created from alarms
- Manual ticket creation
- Priority assignment
- Due date tracking
- Assignment to engineers
- Comments and attachments
- Status workflow (open, in-progress, resolved, closed)

### 6. Dashboard & Analytics

**Overview Dashboard**:
- System statistics
- Machine status summary
- Sensor statistics
- Prediction statistics
- Real-time charts
- Live data table

**Machine Dashboard**:
- Machine details and status
- Sensor readings
- Recent predictions
- Active alarms
- Historical trends

**Sensor Analytics**:
- Trend analysis (1h, 6h, 24h, 7d, 30d)
- Historical data visualization
- Threshold visualization
- Status timeline

### 7. Reporting

**Report Generation**:
- PDF reports
- CSV exports
- Excel exports (CSV format)
- Date range filtering
- Machine-specific reports

**Report Content**:
- Sensor data summary
- Alarm history
- Prediction statistics
- Machine performance metrics

### 8. Audit Logging

**Comprehensive Audit Trail**:
- All user actions logged
- Resource changes tracked
- IP address and user agent capture
- Searchable and filterable logs
- Admin-only access

### 9. System Settings

**Configurable Settings**:
- System-wide configuration
- Category-based organization
- Public/private settings
- Admin-managed updates

### 10. Webhooks

**External Integration**:
- Event-driven webhooks
- Configurable endpoints
- Event subscriptions
- Retry mechanism
- HMAC signature support

**Supported Events**:
- Alarm events (critical/warning)
- Prediction events (anomalies)
- Machine status changes

### 11. Notifications

**Email Notifications** (Optional):
- Gmail SMTP support
- Test email functionality
- Alarm notifications
- Prediction alerts
- Password reset emails

**Webhook Notifications**:
- Real-time event delivery
- Configurable endpoints
- Retry on failure

### 12. File Attachments

**Attachment Support**:
- Upload files to alarms/tickets
- File type validation
- Secure file storage
- Download functionality

### 13. Comments System

**Collaborative Comments**:
- Comments on alarms
- Comments on tickets
- User attribution
- Timestamp tracking

### 14. Real-Time Updates

**WebSocket/SSE Support**:
- Live data streaming
- Event notifications
- Dashboard auto-refresh
- Connection management

### 15. Health Monitoring

**System Health**:
- Service health checks
- Database connectivity
- MQTT broker status
- AI service status
- Comprehensive status endpoint

---

## Data Flow & Working Process

### 1. Sensor Data Ingestion Flow

```
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│Simulator│─────▶│  MQTT    │─────▶│ Backend │─────▶│ Database │
│         │      │  Broker  │      │Consumer │      │          │
└──────────┘      └──────────┘      └──────────┘      └──────────┘
```

**Process**:
1. Simulator generates sensor data
2. Data published to MQTT topics (`factory/#`, `edge/#`)
3. Backend MQTT consumer receives messages
4. Messages queued for processing
5. Data validated and stored in `sensor_data` table
6. Thresholds checked, alarms generated if needed
7. AI service called for anomaly detection
8. Predictions stored and alarms created if anomalies detected

### 2. Prediction Workflow

```
Sensor Data → Feature Extraction → AI Service → Prediction → Alarm (if needed)
```

**Detailed Process**:
1. Sensor data received via MQTT
2. Backend extracts features (25 features)
3. Features sent to AI service
4. AI service processes with Isolation Forest
5. Rule-based fallback if model unavailable
6. Prediction stored in database
7. Alarm created if prediction indicates anomaly
8. Ticket auto-created for critical alarms
9. Notifications sent (email/webhook)

### 3. User Interaction Flow

```
User Login → JWT Token → API Request → RBAC Check → Business Logic → Response
```

**Process**:
1. User logs in via `/users/login`
2. Backend validates credentials
3. JWT tokens issued (access + refresh)
4. Frontend stores tokens
5. API requests include Bearer token
6. Backend validates token and checks role
7. Request processed based on permissions
8. Response returned to frontend
9. Frontend updates UI

### 4. Dashboard Update Flow

```
Frontend → API Polling (10s) → Backend → Database → Response → UI Update
```

**Process**:
1. Dashboard component mounts
2. Initial data fetch (parallel requests)
3. Auto-refresh every 10 seconds
4. Backend queries database
5. Cached responses (30s TTL) for performance
6. Data returned to frontend
7. React Query updates state
8. UI re-renders with new data

### 5. Alarm Resolution Flow

```
Alarm Created → Engineer Notified → Ticket Created → Work Performed → Alarm Resolved
```

**Process**:
1. Alarm auto-created from threshold/prediction
2. Email/webhook notification sent
3. Ticket auto-created (if severity >= warning)
4. Engineer assigned and notified
5. Work performed, comments added
6. Alarm resolved with notes
7. Ticket updated/closed
8. Audit log entry created

---

## Installation & Setup

### Prerequisites

- **Docker Desktop** installed and running
- **Ports available**: 3000, 8000, 8001, 1883, 5432
- **Minimum 4GB RAM** recommended
- **10GB disk space** for Docker images and data

### Quick Setup

1. **Clone/Navigate to Project**:
   ```bash
   cd "Predictive Maintenance"
   ```

2. **Configure Environment** (Optional):
   ```bash
   # Copy example env file
   cp backend/env.example backend/.env
   
   # Edit backend/.env with your settings
   # At minimum, update JWT_SECRET for production
   ```

3. **Start Services**:
   ```bash
   docker-compose up --build -d
   ```

4. **Wait for Initialization** (1-2 minutes):
   - Database migrations run automatically
   - Demo users created automatically
   - Services become healthy

5. **Verify Services**:
   ```bash
   docker-compose ps
   # All services should show "Up"
   ```

6. **Access Application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - System Status: http://localhost:8000/status

---

## Running the System

### Start All Services

```bash
# Build and start (detached mode)
docker-compose up --build -d

# Start without rebuild
docker-compose up -d

# Start with logs visible
docker-compose up
```

### Stop Services

```bash
# Stop services (keeps data)
docker-compose stop

# Stop and remove containers (keeps volumes)
docker-compose down

# Stop and remove everything including volumes
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f ai-service

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Rebuild Services

```bash
# Rebuild all
docker-compose build

# Rebuild specific service
docker-compose build backend

# Rebuild and restart
docker-compose up --build -d backend
```

### Execute Commands in Containers

```bash
# Run command in backend
docker-compose exec backend python -m app.tasks.seed_demo_data

# Access database
docker-compose exec postgres psql -U pm_user -d pm_db

# Access backend shell
docker-compose exec backend bash
```

---

## Testing Guide

### 1. System Health Checks

**Backend Health**:
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"Predictive Maintenance Backend",...}

curl http://localhost:8000/status
# Expected: Comprehensive system status with all services
```

**AI Service Health**:
```bash
curl http://localhost:8001/health
# Expected: {"status":"healthy","model_loaded":true,...}
```

**Frontend**:
- Open http://localhost:3000
- Should load login page without errors

### 2. Authentication Testing

**Login Test**:
```bash
curl -X POST http://localhost:8000/users/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"
```

**Expected Response**:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Test Protected Endpoint**:
```bash
# Use token from login response
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. MQTT Data Flow Testing

**Check Simulator**:
```bash
docker-compose logs simulator
# Should show messages being published
```

**Check MQTT Consumer**:
```bash
docker-compose logs backend | grep MQTT
# Should show messages being received and processed
```

**Verify Data in Database**:
```bash
# Via API (with auth token)
curl http://localhost:8000/sensor-data/logs?limit=10 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. AI Prediction Testing

**Check Predictions**:
```bash
curl http://localhost:8000/predictions?limit=10 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Check AI Service Status**:
```bash
curl http://localhost:8000/ai/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Dashboard Testing

**Test Dashboard Endpoints**:
```bash
# Overview
curl http://localhost:8000/dashboard/overview \
  -H "Authorization: Bearer YOUR_TOKEN"

# Machine stats
curl http://localhost:8000/dashboard/machines/stats \
  -H "Authorization: Bearer YOUR_TOKEN"

# Sensor stats
curl http://localhost:8000/dashboard/sensors/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 6. Report Generation Testing

**Generate Report**:
```bash
curl -X POST http://localhost:8000/reports/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "csv",
    "date_from": "2025-12-01T00:00:00Z",
    "date_to": "2025-12-09T23:59:59Z"
  }'
```

**Download Report**:
- Use the `report_name` from response
- Access via: http://localhost:8000/reports/download/{report_name}

### 7. Frontend Testing

**Manual Testing Checklist**:
- [ ] Login with demo users (admin/engineer/viewer)
- [ ] View dashboard and verify data loads
- [ ] Check real-time updates (wait 10 seconds)
- [ ] Navigate to Machines page
- [ ] Navigate to Sensors page
- [ ] View Predictions
- [ ] View Alarms
- [ ] Create/Update/Resolve alarm
- [ ] View Tickets
- [ ] Generate and download report
- [ ] Check AI Service status
- [ ] Check MQTT status
- [ ] Test notifications (email/webhook)

### 8. Integration Testing

**End-to-End Flow**:
1. Start all services
2. Wait for simulator to publish data
3. Verify sensor data appears in database
4. Verify predictions are generated
5. Verify alarms are created (if thresholds exceeded)
6. Verify tickets are auto-created
7. Login to frontend
8. Verify dashboard shows data
9. Verify alarms/tickets appear
10. Resolve an alarm
11. Verify ticket updates

### 9. Performance Testing

**Load Test** (Optional):
```bash
# Install Apache Bench
# Test API endpoint
ab -n 1000 -c 10 -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/dashboard/overview
```

**Monitor Resources**:
```bash
# Docker stats
docker stats

# Service logs for errors
docker-compose logs --tail=100 | grep -i error
```

---

## API Documentation

### Base URL
- **Development**: http://localhost:8000
- **Production**: Configure via environment

### Authentication

All endpoints (except `/health`, `/docs`, `/openapi.json`) require authentication:

```
Authorization: Bearer <access_token>
```

### Key Endpoints

#### Health & Status
- `GET /` - System information
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe
- `GET /status` - Comprehensive system status

#### Authentication
- `POST /users/login` - Login and get tokens
- `POST /users/refresh` - Refresh access token
- `GET /users/me` - Get current user profile
- `PATCH /users/me` - Update profile

#### Dashboard
- `GET /dashboard/overview` - Overview statistics
- `GET /dashboard/machines/stats` - Machine statistics
- `GET /dashboard/sensors/stats` - Sensor statistics
- `GET /dashboard/predictions/stats` - Prediction statistics

#### Machines
- `GET /machines` - List machines
- `GET /machines/{id}` - Get machine details
- `GET /machines/{id}/summary` - Machine summary
- `POST /machines` - Create machine (Engineer+)
- `PATCH /machines/{id}` - Update machine (Engineer+)
- `DELETE /machines/{id}` - Delete machine (Engineer+)

#### Sensors
- `GET /sensors` - List sensors
- `GET /sensors/{id}` - Get sensor details
- `GET /sensors/{id}/trend` - Sensor trend data
- `POST /sensors` - Create sensor (Engineer+)
- `PATCH /sensors/{id}` - Update sensor (Engineer+)

#### Predictions
- `GET /predictions` - List predictions
- `GET /predictions/{id}` - Get prediction details
- `GET /predictions/{id}/explain` - Prediction explanation

#### Alarms
- `GET /alarms` - List alarms
- `GET /alarms/{id}` - Get alarm details
- `POST /alarms/{id}/resolve` - Resolve alarm
- `POST /alarms/{id}/comments` - Add comment

#### Tickets
- `GET /tickets` - List tickets
- `GET /tickets/{id}` - Get ticket details
- `POST /tickets` - Create ticket
- `PATCH /tickets/{id}` - Update ticket

#### Reports
- `POST /reports/generate` - Generate report
- `GET /reports/download/{filename}` - Download report

#### AI Service
- `GET /ai/status` - AI service status (Engineer+)
- `POST /ai/retrain` - Retrain model (Admin)
- `GET /ai/logs` - AI service logs (Engineer+)

#### MQTT
- `GET /mqtt/status` - MQTT broker status (Engineer+)

#### Notifications
- `POST /notifications/test-email` - Test email
- `POST /notifications/test-webhook` - Test webhook

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## Configuration

### Environment Variables

**Backend Configuration** (`backend/.env`):

```bash
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=pm_user
POSTGRES_PASSWORD=pm_pass
POSTGRES_DB=pm_db

# JWT Authentication
JWT_SECRET=your-secret-key-here  # CHANGE IN PRODUCTION
JWT_ALGORITHM=HS256
JWT_EXP_MINUTES=60

# AI Service
AI_SERVICE_URL=http://ai-service:8000

# MQTT
MQTT_BROKER_HOST=mqtt
MQTT_BROKER_PORT=1883
MQTT_TOPICS=factory/#,edge/#

# Email (Optional - Gmail)
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-email@gmail.com
EMAIL_SMTP_PASS=your-app-password  # Use Gmail App Password
NOTIFICATION_EMAIL_TO=recipient@example.com

# Slack (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### Gmail SMTP Setup

1. Enable 2-Step Verification: https://myaccount.google.com/security
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Select "Mail" and your device
4. Copy the 16-character password
5. Use in `EMAIL_SMTP_PASS` (NOT your regular password)

### Docker Configuration

**docker-compose.yml**:
- Service definitions
- Network configuration
- Volume mounts
- Environment variables
- Port mappings

**Customization**:
- Modify ports if conflicts exist
- Adjust resource limits
- Add additional services
- Configure production settings

---

## Troubleshooting

### Services Won't Start

**Symptoms**: Containers exit immediately or show errors

**Solutions**:
1. Check Docker Desktop is running
2. Verify ports are not in use:
   ```bash
   netstat -an | findstr "3000 8000 8001 1883 5432"
   ```
3. Check logs: `docker-compose logs [service-name]`
4. Verify disk space: `docker system df`
5. Rebuild: `docker-compose build --no-cache`

### Database Connection Issues

**Symptoms**: Backend can't connect to database

**Solutions**:
1. Wait 30-60 seconds for database initialization
2. Check database logs: `docker-compose logs postgres`
3. Verify environment variables match
4. Check network: `docker network ls`
5. Restart database: `docker-compose restart postgres`

### Frontend Not Loading

**Symptoms**: Blank page or connection errors

**Solutions**:
1. Wait 1-2 minutes for services to fully start
2. Check backend: http://localhost:8000/health
3. Check browser console (F12) for errors
4. Verify nginx proxy: `docker-compose logs frontend`
5. Rebuild frontend: `docker-compose build frontend`

### MQTT Not Receiving Data

**Symptoms**: No sensor data in database

**Solutions**:
1. Check simulator: `docker-compose logs simulator`
2. Check MQTT broker: `docker-compose logs mqtt`
3. Check backend consumer: `docker-compose logs backend | grep MQTT`
4. Verify topics match configuration
5. Test MQTT manually: Use MQTT client to publish test message

### AI Service Not Responding

**Symptoms**: Predictions not generated

**Solutions**:
1. Check AI service: http://localhost:8001/health
2. Check logs: `docker-compose logs ai-service`
3. Verify model files exist in `ai_service/models/`
4. Check backend connection: `docker-compose logs backend | grep ai`
5. Restart AI service: `docker-compose restart ai-service`

### Email Not Sending

**Symptoms**: Email test fails with authentication error

**Solutions**:
1. Verify Gmail App Password is used (not regular password)
2. Check 2-Step Verification is enabled
3. Verify SMTP settings in `backend/.env`
4. Check error message for specific issue
5. Email is optional - system works without it

### Performance Issues

**Symptoms**: Slow responses, high memory usage

**Solutions**:
1. Check resource usage: `docker stats`
2. Increase Docker memory limit
3. Check database query performance
4. Review cache settings
5. Optimize dashboard refresh interval

### Common Error Messages

**"Not Found" errors**:
- Check endpoint URL is correct
- Verify authentication token is valid
- Check API documentation at `/docs`

**"Database connection failed"**:
- Wait for database to initialize
- Check database container is running
- Verify connection string

**"MQTT connection failed"**:
- Check MQTT broker is running
- Verify network connectivity
- Check topic subscriptions

---

## Production Deployment

### Security Checklist

- [ ] Change `JWT_SECRET` to strong random value
- [ ] Use strong database passwords
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Use secrets management (not .env files)
- [ ] Enable MQTT authentication
- [ ] Configure CORS properly
- [ ] Set up monitoring and alerting
- [ ] Regular backups of database
- [ ] Update dependencies regularly

### Performance Optimization

- [ ] Use Redis for distributed caching
- [ ] Configure database connection pooling
- [ ] Enable database query optimization
- [ ] Use CDN for frontend assets
- [ ] Configure load balancing
- [ ] Set up horizontal scaling
- [ ] Monitor resource usage
- [ ] Optimize Docker images

### Monitoring

- [ ] Set up health check monitoring
- [ ] Configure log aggregation
- [ ] Set up error tracking
- [ ] Monitor database performance
- [ ] Track API response times
- [ ] Monitor MQTT message rates
- [ ] Set up alerting for critical issues

---

## Support & Resources

### Documentation Files

- `README.md` - Quick start and overview
- `QUICK_START.md` - Quick start guide
- `PROJECT_STRUCTURE.md` - Detailed project structure
- `docs/architecture.md` - System architecture
- `docs/db-schema.md` - Database schema
- `docs/tests.md` - Testing documentation

### API Documentation

- Interactive API docs: http://localhost:8000/docs
- OpenAPI schema: http://localhost:8000/openapi.json

### System Status

- System status: http://localhost:8000/status
- Health check: http://localhost:8000/health

---

## Conclusion

The Predictive Maintenance Platform is a comprehensive, production-ready solution for industrial IoT monitoring and predictive maintenance. With its microservices architecture, AI-powered analytics, and modern web interface, it provides a complete solution for proactive maintenance strategies.

**Key Strengths**:
- Scalable microservices architecture
- Real-time data processing
- AI-powered anomaly detection
- Comprehensive feature set
- Enterprise-ready security
- Easy deployment with Docker

**Use Cases**:
- Manufacturing facilities
- Industrial plants
- Equipment monitoring
- Predictive maintenance programs
- IoT sensor data management

---

**Version**: 1.0.0  
**Last Updated**: December 2025  
**License**: Proprietary

