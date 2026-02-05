# Predictive Maintenance Platform - Project Structure

## 📁 Complete Folder Structure

```
Predictive Maintenance/
├── 📄 docker-compose.yml          # Main orchestration file
├── 📄 README.md                    # Project documentation
│
├── 🗄️ backend/                     # FastAPI Backend Service
│   ├── 📄 Dockerfile               # Backend container definition
│   ├── 📄 requirements.txt         # Python dependencies
│   ├── 📄 alembic.ini             # Database migration config
│   │
│   ├── 📁 alembic/                 # Database migrations
│   │   ├── 📄 env.py              # Migration environment
│   │   └── 📁 versions/            # Migration scripts
│   │       ├── 0001_initial.py
│   │       ├── 0002_add_audit_settings_webhook.py
│   │       └── 0003_add_auth_roles_attachments_comments_jobs.py
│   │
│   ├── 📁 app/                     # Main application code
│   │   ├── 📄 main.py             # FastAPI app entry point
│   │   │
│   │   ├── 📁 api/                 # API routes
│   │   │   ├── 📄 dependencies.py  # Auth, DB session dependencies
│   │   │   └── 📁 routers/         # API endpoint modules
│   │   │       ├── users.py       # Authentication & user management
│   │   │       ├── machines.py    # Machine CRUD
│   │   │       ├── sensors.py     # Sensor management
│   │   │       ├── sensor_data.py # Sensor data ingestion
│   │   │       ├── predictions.py # AI predictions
│   │   │       ├── alarms.py      # Alarm management
│   │   │       ├── tickets.py     # Ticket system
│   │   │       ├── dashboard.py  # Dashboard overview
│   │   │       ├── health.py      # Health checks
│   │   │       ├── realtime.py    # WebSocket/SSE
│   │   │       ├── roles.py      # RBAC
│   │   │       ├── attachments.py # File attachments
│   │   │       ├── metrics.py    # Prometheus metrics
│   │   │       └── jobs.py        # Background jobs
│   │   │
│   │   ├── 📁 core/                # Core configuration
│   │   │   ├── 📄 config.py       # Settings (env vars)
│   │   │   └── 📄 security.py     # JWT, password hashing
│   │   │
│   │   ├── 📁 db/                  # Database setup
│   │   │   ├── 📄 base.py         # SQLAlchemy base
│   │   │   └── 📄 session.py      # Async session factory
│   │   │
│   │   ├── 📁 models/              # SQLAlchemy models
│   │   │   ├── 📄 base.py         # Base model class
│   │   │   ├── 📄 user.py         # User model
│   │   │   ├── 📄 machine.py      # Machine model
│   │   │   ├── 📄 sensor.py      # Sensor model
│   │   │   ├── 📄 sensor_data.py # Sensor readings
│   │   │   ├── 📄 prediction.py  # AI predictions
│   │   │   ├── 📄 alarm.py       # Alarms
│   │   │   ├── 📄 ticket.py      # Tickets
│   │   │   ├── 📄 audit_log.py   # Audit trail
│   │   │   ├── 📄 settings.py     # System settings
│   │   │   ├── 📄 webhook.py     # Webhooks
│   │   │   ├── 📄 password_reset.py # Password reset tokens
│   │   │   ├── 📄 role.py        # RBAC roles
│   │   │   ├── 📄 attachment.py  # File attachments
│   │   │   ├── 📄 comment.py     # Comments
│   │   │   └── 📄 job.py         # Background jobs
│   │   │
│   │   ├── 📁 schemas/             # Pydantic schemas
│   │   │   ├── 📄 base.py        # Base schema
│   │   │   ├── 📄 user.py        # User schemas
│   │   │   ├── 📄 machine.py     # Machine schemas
│   │   │   ├── 📄 sensor.py      # Sensor schemas
│   │   │   ├── 📄 prediction.py  # Prediction schemas
│   │   │   ├── 📄 alarm.py       # Alarm schemas
│   │   │   ├── 📄 ticket.py      # Ticket schemas
│   │   │   └── ... (other schemas)
│   │   │
│   │   ├── 📁 services/            # Business logic layer
│   │   │   ├── 📄 user_service.py
│   │   │   ├── 📄 machine_service.py
│   │   │   ├── 📄 sensor_service.py
│   │   │   ├── 📄 prediction_service.py
│   │   │   ├── 📄 alarm_service.py
│   │   │   ├── 📄 notification_service.py
│   │   │   └── ... (other services)
│   │   │
│   │   ├── 📁 mqtt/                # MQTT integration
│   │   │   └── 📄 consumer.py     # MQTT message consumer
│   │   │
│   │   └── 📁 tasks/               # Background tasks
│   │       ├── 📄 seed_demo_data.py # Demo data seeding
│   │       └── 📄 seed.py
│   │
│   └── 📁 scripts/                 # Utility scripts
│       └── 📄 wait_for_db.py      # DB connection retry
│
├── 🎨 frontend/                     # React Frontend
│   ├── 📄 Dockerfile               # Production build
│   ├── 📄 Dockerfile.dev           # Development build
│   ├── 📄 package.json             # NPM dependencies
│   ├── 📄 vite.config.ts           # Vite configuration
│   ├── 📄 tsconfig.json            # TypeScript config
│   ├── 📄 nginx.conf               # Nginx config
│   │
│   └── 📁 src/                      # Source code
│       ├── 📄 main.tsx             # Entry point
│       ├── 📄 App.tsx              # Root component
│       │
│       ├── 📁 pages/                # Page components
│       │   ├── 📄 Login.tsx        # Login page
│       │   └── 📄 Dashboard.tsx    # Main dashboard
│       │
│       ├── 📁 components/          # Reusable components
│       │   ├── 📄 Topbar.tsx      # Navigation bar
│       │   ├── 📄 LoadingSkeleton.tsx # Loading states
│       │   └── 📄 ErrorToast.tsx  # Error notifications
│       │
│       ├── 📁 contexts/            # React contexts
│       │   └── 📄 AuthContext.tsx  # Authentication state
│       │
│       ├── 📁 hooks/                # Custom hooks
│       │   ├── 📄 useLiveData.ts   # Data fetching hooks
│       │   ├── 📄 useWebSocket.ts  # WebSocket hook
│       │   └── 📄 useSSE.ts        # SSE hook
│       │
│       ├── 📁 api.ts                # API client (Axios)
│       └── 📁 styles.css            # Global styles
│
├── 🤖 ai_service/                   # AI/ML Service
│   ├── 📄 Dockerfile
│   ├── 📄 main.py                  # FastAPI service
│   ├── 📄 model_manager.py        # Model loading
│   ├── 📄 features.py              # Feature extraction
│   ├── 📄 train_model.py          # Model training
│   ├── 📁 models/                  # Trained models
│   │   ├── isolation_forest.pkl
│   │   ├── scaler.pkl
│   │   └── metadata.json
│   └── 📁 data/                    # Training data
│
├── 📡 simulator/                    # MQTT Simulator
│   ├── 📄 Dockerfile
│   └── 📄 publish_sim.py          # Sensor data simulator
│
├── 📡 mqtt/                         # MQTT Configuration
│   └── 📄 mosquitto.conf           # Mosquitto config
│
└── 📚 docs/                         # Documentation
    ├── 📄 architecture.md
    ├── 📄 db-schema.md
    └── 📄 tests.md
```

## 🏗️ Architecture Overview

### **Backend (FastAPI)**
- **Framework**: FastAPI with async SQLAlchemy
- **Database**: TimescaleDB (PostgreSQL extension)
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Authentication**: JWT (access + refresh tokens)
- **Authorization**: RBAC (admin, engineer, viewer)
- **Real-time**: WebSocket + Server-Sent Events
- **MQTT**: Paho MQTT client for sensor ingestion

### **Frontend (React)**
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: React Query (TanStack Query)
- **Routing**: React Router
- **Real-time**: WebSocket + SSE hooks
- **HTTP Client**: Axios

### **AI Service (FastAPI)**
- **ML Model**: Isolation Forest (scikit-learn)
- **Purpose**: Anomaly detection on sensor data
- **Input**: Sensor readings (temperature, vibration, etc.)
- **Output**: Anomaly score + prediction

### **Database Schema**
- **Core Tables**: user, machine, sensor, sensor_data
- **AI Tables**: prediction, modelregistry
- **Operations**: alarm, ticket
- **System**: auditlog, settings, webhook
- **Auth**: passwordresettoken, role
- **Features**: attachment, comment, job

### **Services & Communication**
- **Backend ↔ Database**: Async SQLAlchemy
- **Backend ↔ AI Service**: HTTP (httpx)
- **Simulator → MQTT**: Paho MQTT
- **MQTT → Backend**: Paho MQTT consumer
- **Backend ↔ Frontend**: REST API + WebSocket/SSE

## 🔄 Data Flow

1. **Sensor Data Ingestion**:
   ```
   Simulator → MQTT Broker → Backend Consumer → Database
   ```

2. **Prediction Workflow**:
   ```
   Sensor Data → Backend → AI Service → Prediction → Database → Alarm (if needed)
   ```

3. **Real-time Updates**:
   ```
   Database Changes → Backend → WebSocket/SSE → Frontend
   ```

4. **User Authentication**:
   ```
   Frontend → Backend /users/login → JWT Tokens → Protected Routes
   ```

## 🐳 Docker Services

1. **postgres**: TimescaleDB database
2. **mqtt**: Eclipse Mosquitto broker
3. **backend**: FastAPI application
4. **ai-service**: ML inference service
5. **frontend**: React app (Nginx)
6. **simulator**: MQTT data generator

## 📊 Key Features

- ✅ JWT Authentication with refresh tokens
- ✅ Role-Based Access Control (RBAC)
- ✅ Real-time sensor data ingestion (MQTT)
- ✅ AI-powered anomaly detection
- ✅ Automatic alarm generation
- ✅ Ticket management system
- ✅ Audit logging
- ✅ WebSocket/SSE for live updates
- ✅ File attachments
- ✅ Comments on alarms/tickets
- ✅ Background job tracking
- ✅ Prometheus metrics
- ✅ Health probes (liveness/readiness)

