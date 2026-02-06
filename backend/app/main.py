import asyncio
from datetime import datetime
from pathlib import Path
import os
from loguru import logger

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.routers import (
    ai,
    alarms,
    attachments,
    audit,
    connections,
    dashboard,
    health,
    history,
    jobs,
    knowledge,
    machine_state,
    machines,
    metrics,
    notifications,
    predictions,
    realtime,
    reports,
    roles,
    sensor_data,
    sensors,
    settings as settings_router,
    system,
    tickets,
    users,
    webhooks,
)
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.services.mssql_extruder_poller import mssql_extruder_poller
from app.services import notification_service
from app.services.incident_manager import incident_manager

settings = get_settings()

app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    debug=settings.debug,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Custom OpenAPI schema to ensure proper version field
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.project_name,
        version="1.0.0",
        description="Predictive Maintenance Platform API - Complete API for managing machines, sensors, predictions, alarms, and more.",
        routes=app.routes,
    )
    # Explicitly set OpenAPI version to 3.1.0
    openapi_schema["openapi"] = "3.1.0"
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Performance optimizations
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB

# Custom exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Provide helpful 404 messages with available endpoints"""
    return JSONResponse(
        status_code=404,
        content={
            "detail": f"Endpoint not found: {request.url.path}",
            "message": "The requested endpoint does not exist. Here are some available endpoints:",
            "available_endpoints": {
                "root": "/",
                "health": "/health",
                "status": "/status",
                "api_docs": "/docs",
                "openapi": "/openapi.json",
                "dashboard": "/dashboard/overview",
                "ai_status": "/ai/status",
                "machines": "/machines",
                "sensors": "/sensors",
                "predictions": "/predictions",
                "alarms": "/alarms",
                "tickets": "/tickets",
                "reports": "/reports/generate"
            },
            "tip": "Visit /docs for the complete API documentation"
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Provide helpful validation error messages"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "message": "The request data is invalid. Please check your input.",
            "errors": exc.errors(),
            "path": str(request.url.path)
        }
    )

reports_dir = settings.reports_dir
reports_dir.mkdir(parents=True, exist_ok=True)

# Include machine_state router first for debugging
logger.info(f"Before machine_state inclusion: {len(app.routes)} routes")
logger.info(f"Machine state router has {len(machine_state.router.routes)} routes")
app.include_router(machine_state.router)
logger.info(f"After machine_state inclusion: {len(app.routes)} routes")

app.include_router(health.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(machines.router)
app.include_router(sensors.router)
app.include_router(sensor_data.router)
app.include_router(predictions.router)
app.include_router(alarms.router)
app.include_router(tickets.router)
app.include_router(reports.router)  # Must be before static mount to handle /reports/download routes
app.include_router(notifications.router)
app.include_router(knowledge.router)
app.include_router(history.router)
app.include_router(dashboard.router)
app.include_router(ai.router)
app.include_router(settings_router.router)
app.include_router(connections.router)
app.include_router(system.router)
app.include_router(webhooks.router)
app.include_router(audit.router)
app.include_router(realtime.router)
app.include_router(attachments.router)
app.include_router(metrics.router)
app.include_router(jobs.router)

# Mount static files AFTER routers so router routes take precedence
app.mount("/reports", StaticFiles(directory=reports_dir), name="reports")


@app.get("/")
async def root():
    """Root endpoint - shows system information and available endpoints"""
    return {
        "service": "Predictive Maintenance Platform",
        "version": "1.0.0",
        "status": "running",
        "message": "Backend API is running successfully",
        "timestamp": datetime.utcnow().isoformat(),
            "endpoints": {
            "health": "/health",
            "status": "/status",
            "api_docs": "/docs",
            "openapi": "/openapi.json",
            "dashboard": "/dashboard/overview",
            "ai_status": "/ai/status"
        },
        "services": {
            "backend": "Running",
            "database": "Check /health/ready",
            "ai_service": "Check /ai/status"
        }
    }


@app.on_event("startup")
async def startup_event():
    # Get the current event loop for async operations
    loop = asyncio.get_event_loop()

    # Optional clean slate reset (MANDATORY for commissioning/testing).
    # Guarded by env var so production deployments are not destructive by default.
    if os.getenv("CLEAN_SLATE_ON_STARTUP", "false").lower() in {"1", "true", "yes"}:
        try:
            from sqlalchemy import delete
            from app.models.ticket import Ticket
            from app.models.alarm import Alarm

            async with AsyncSessionLocal() as session:
                await session.execute(delete(Ticket))
                await session.execute(delete(Alarm))
                await session.commit()
            incident_manager.reset_runtime_state()
            logger.warning("Clean-slate reset applied on startup (alarms/tickets cleared)")
        except Exception as e:
            logger.error(f"Clean-slate reset failed: {e}")

    # ENABLED: MQTT and OPC UA for real sensor data processing
    # NOTE:
    # The platform was originally designed to ingest live data via MQTT and OPC UA.
    # For the current extruder deployment, the canonical data source is MSSQL,
    # so we rely on the MSSQL extruder poller instead and keep MQTT/OPC UA disabled
    # to reduce operational complexity.
    #
    # If you ever need to re-enable MQTT/OPC UA ingestion, restore the
    # mqtt_ingestor/opcua_connector imports above and the start/stop calls here.
    logger.info("MQTT and OPC UA ingestion DISABLED - using MSSQL extruder poller as primary data source")
    
    # DISABLED: Direct sensor data simulation - using real sensor data instead
    # from app.tasks.sensor_data_simulator import start_sensor_data_simulation
    # loop.create_task(start_sensor_data_simulation(interval_seconds=2))
    # logger.info("Direct sensor data simulation DISABLED - using real sensor data")
    
    # Optional: MSSQL read-only extruder poller (no OPC UA). Opt-in via env vars.
    mssql_extruder_poller.start(loop)
    await asyncio.sleep(1)
    logger.info("Startup complete - real sensor data processing ready")

    # ENABLED: Demo machines for testing machine state detection
    try:
        from app.tasks.seed_demo_data import seed_demo_users, seed_sample_machines

        logger.info("Ensuring demo users exist (admin/engineer/viewer)")
        await seed_demo_users()
        logger.info("Demo users verified/created")
        
        logger.info("Ensuring demo machines exist for state testing")
        await seed_sample_machines()
        logger.info("Demo machines created for machine state detection")
    except Exception as e:
        # Don't block startup if seeding fails (e.g., schema differences)
        logger.error(f"Failed to ensure demo data: {e}")
    
    # Verify email configuration if available (non-blocking best-effort check)
    verify_email = getattr(notification_service, "verify_email_transport", None)
    if verify_email:
        await verify_email()


@app.on_event("shutdown")
async def shutdown_event():
    # MSSQL poller shutdown
    await mssql_extruder_poller.stop()
    logger.info("Backend shutdown complete - MSSQL-based real sensor data processing stopped")

