# Predictive Maintenance Platform

A production-grade industrial IoT platform for predictive maintenance. Provides real-time sensor data ingestion, AI-powered anomaly detection, and a modern web dashboard for industrial equipment monitoring.

## Quick Start

### Prerequisites

- Docker Desktop installed and running
- Available ports: 3000, 8000, 8001, 1883, 5432

### Start the Platform

```bash
# Build and start all services
docker-compose up --build -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Access the Application

- Frontend Dashboard: http://localhost:3000
- Backend API Documentation: http://localhost:8000/docs
- Backend Status: http://localhost:8000/status
- AI Service Health: http://localhost:8001/health

### Demo Login Credentials

- Admin: `admin@example.com` / `admin123`
- Engineer: `engineer@example.com` / `engineer123`
- Viewer: `viewer@example.com` / `viewer123`

## System Architecture

### Services

1. Backend (FastAPI) - Port 8000
   - RESTful API with async SQLAlchemy
   - JWT authentication and RBAC
   - MQTT consumer for sensor data
   - Real-time WebSocket/SSE support

2. Frontend (React + Vite) - Port 3000
   - React 18 with TypeScript
   - Tailwind CSS styling
   - React Query for data fetching
   - Real-time dashboard updates

3. AI Service (FastAPI) - Port 8001
   - Isolation Forest anomaly detection
   - Rule-based fallback system
   - Real-time prediction engine

4. Database (TimescaleDB) - Port 5432
   - PostgreSQL 15 with Timescale extension
   - Time-series optimized storage
   - Async SQLAlchemy ORM

5. MQTT Broker (Mosquitto) - Port 1883
   - Eclipse Mosquitto broker
   - Sensor data ingestion

6. Simulator - Background service
   - Generates realistic sensor data
   - Publishes to MQTT topics

## Project Structure

```
Predictive Maintenance/
├── backend/              # FastAPI backend service
│   ├── app/             # Application code
│   ├── alembic/         # Database migrations
│   └── scripts/         # Utility scripts
├── frontend/            # React frontend
│   └── src/            # Source code
├── ai_service/          # AI/ML service
├── simulator/           # MQTT data simulator
├── mqtt/                # MQTT configuration
├── docs/                # Documentation
└── docker-compose.yml   # Docker orchestration
```

See `PROJECT_STRUCTURE.md` for detailed structure.

## Configuration

### Environment Variables

Backend configuration is in `backend/env.example`. Copy to `backend/.env` and customize:

```bash
# Database
POSTGRES_USER=pm_user
POSTGRES_PASSWORD=pm_pass
POSTGRES_DB=pm_db

# JWT
JWT_SECRET=your-secret-key-here
JWT_EXP_MINUTES=60

# AI Service
AI_SERVICE_URL=http://ai-service:8000

# MQTT
MQTT_BROKER_HOST=mqtt
MQTT_BROKER_PORT=1883
```

## API Documentation

### Key Endpoints

- `GET /` - System information and status
- `GET /health` - Health check
- `GET /status` - Comprehensive system status
- `GET /docs` - Interactive API documentation
- `GET /dashboard/overview` - Dashboard statistics
- `GET /machines` - List machines
- `GET /sensors` - List sensors
- `GET /predictions` - Get predictions
- `GET /alarms` - List alarms
- `POST /reports/generate` - Generate reports

### Authentication

All endpoints (except `/health`, `/docs`, `/openapi.json`) require JWT authentication:

```bash
# Login
POST /users/login
{
  "email": "admin@example.com",
  "password": "admin123"
}

# Use token in requests
Authorization: Bearer <access_token>
```

## Development

### Local Development (Without Docker)

Backend:
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

AI Service:
```bash
cd ai_service
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Database Migrations

```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Seed Demo Data

```bash
docker-compose exec backend python -m app.tasks.seed_demo_data
```

## Testing

```bash
# Backend tests
cd backend
pytest

# Check service health
curl http://localhost:8000/health
curl http://localhost:8000/status
curl http://localhost:8001/health
```

## Features

### Core Features

- Real-time Sensor Data Ingestion - MQTT-based sensor data collection
- AI-Powered Anomaly Detection - Isolation Forest with rule-based fallback
- Predictive Maintenance - Failure prediction and RUL estimation
- Alarm Management - Automatic alarm generation and resolution
- Ticket System - Work order and maintenance ticket management
- Role-Based Access Control - Admin, Engineer, Viewer roles
- Dashboard - Real-time monitoring and statistics
- Reports - PDF/CSV report generation
- Audit Logging - Comprehensive activity tracking
- Webhooks - External system integration
- File Attachments - Support for ticket/alarm attachments
- Comments - Collaborative comments on alarms/tickets

### Real-time Features

- WebSocket support for live updates
- Server-Sent Events (SSE) for event streaming
- Live dashboard with auto-refresh
- Real-time sensor data visualization

## Security

- JWT-based authentication with refresh tokens
- Password hashing with bcrypt
- Role-based access control (RBAC)
- SQL injection protection (SQLAlchemy ORM)
- CORS configuration
- Input validation with Pydantic

## Monitoring

### Health Checks

- `GET /health` - Basic health check
- `GET /health/ready` - Readiness probe (checks database)
- `GET /health/live` - Liveness probe
- `GET /status` - Comprehensive system status

### Metrics

- `GET /metrics` - Prometheus-compatible metrics
- `GET /ai/status` - AI service status and metrics
- `GET /mqtt/status` - MQTT broker and consumer status

## Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service-name]

# Rebuild specific service
docker-compose build [service-name]

# Restart service
docker-compose restart [service-name]

# Execute command in container
docker-compose exec backend python -m app.tasks.seed_demo_data
```

## Troubleshooting

### Services Won't Start

1. Check Docker Desktop is running
2. Verify ports are not in use: `netstat -an | findstr "3000 8000 8001"`
3. Check logs: `docker-compose logs [service-name]`

### Database Connection Issues

1. Wait for database to initialize (30-60 seconds)
2. Check database logs: `docker-compose logs postgres`
3. Verify environment variables in `backend/.env`

### Frontend Not Loading

1. Wait 1-2 minutes for services to fully start
2. Check backend: http://localhost:8000/health
3. Check browser console (F12) for errors
4. Verify nginx proxy configuration

### MQTT Not Receiving Data

1. Check MQTT broker: `docker-compose logs mqtt`
2. Check simulator: `docker-compose logs simulator`
3. Verify MQTT topics in backend configuration

## Additional Documentation

- `QUICK_START.md` - Quick start guide
- `PROJECT_STRUCTURE.md` - Detailed project structure
- `docs/architecture.md` - System architecture
- `docs/db-schema.md` - Database schema
- `docs/tests.md` - Testing documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is proprietary software.

## Support

For issues and questions:
- Check the troubleshooting section
- Review service logs
- Check API documentation at `/docs`
- Verify system status at `/status`
