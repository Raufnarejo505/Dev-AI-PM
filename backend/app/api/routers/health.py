from datetime import datetime
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.core.config import get_settings
from app.mqtt.consumer import mqtt_ingestor

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health")
def health():
    """Basic health check"""
    return {
        "status": "ok",
        "service": "Predictive Maintenance Backend",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "✅ Backend service is running successfully"
    }


@router.get("/health/live")
def liveness():
    """Liveness probe - indicates service is running"""
    return {
        "status": "alive",
        "service": "Predictive Maintenance Backend",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "✅ Service is alive and running"
    }


@router.get("/health/ready")
async def readiness(session: AsyncSession = Depends(get_session)):
    """Readiness probe - indicates service is ready to accept traffic"""
    try:
        # Check database connection
        await session.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "service": "Predictive Maintenance Backend",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "✅ Service is ready to accept requests"
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "service": "Predictive Maintenance Backend",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "message": "⚠️ Service is not ready - database connection failed"
        }


@router.get("/status")
async def system_status(session: AsyncSession = Depends(get_session)):
    """Comprehensive system status including all services"""
    status = {
        "service": "Predictive Maintenance Platform",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "backend": {
            "status": "running",
            "message": "✅ Backend service is operational"
        },
        "database": {
            "status": "unknown",
            "message": "Checking..."
        },
        "mqtt": {
            "status": "unknown",
            "message": "Checking...",
            "connected": mqtt_ingestor.is_connected() if hasattr(mqtt_ingestor, 'is_connected') else False
        },
        "ai_service": {
            "status": "unknown",
            "message": "Checking...",
            "url": settings.ai_service_url
        },
        "endpoints": {
            "api_docs": "/docs",
            "health": "/health",
            "status": "/status",
            "dashboard": "/dashboard/overview"
        }
    }
    
    # Check database
    try:
        await session.execute(text("SELECT 1"))
        status["database"]["status"] = "connected"
        status["database"]["message"] = "✅ Database connection successful"
    except Exception as e:
        status["database"]["status"] = "disconnected"
        status["database"]["message"] = f"❌ Database connection failed: {str(e)}"
    
    # Check MQTT
    try:
        if hasattr(mqtt_ingestor, 'is_connected'):
            is_connected = mqtt_ingestor.is_connected()
            status["mqtt"]["connected"] = is_connected
            if is_connected:
                status["mqtt"]["status"] = "connected"
                status["mqtt"]["message"] = "✅ MQTT broker connected"
            else:
                status["mqtt"]["status"] = "disconnected"
                status["mqtt"]["message"] = "⚠️ MQTT broker not connected"
        else:
            status["mqtt"]["status"] = "unknown"
            status["mqtt"]["message"] = "⚠️ MQTT status unavailable"
    except Exception as e:
        status["mqtt"]["status"] = "error"
        status["mqtt"]["message"] = f"❌ MQTT check failed: {str(e)}"
    
    # Check AI Service
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{settings.ai_service_url}/health")
                if response.status_code == 200:
                    status["ai_service"]["status"] = "running"
                    status["ai_service"]["message"] = "✅ AI service is operational"
                    try:
                        ai_data = response.json()
                        if isinstance(ai_data, dict):
                            status["ai_service"]["details"] = ai_data
                    except:
                        pass
                else:
                    status["ai_service"]["status"] = "unhealthy"
                    status["ai_service"]["message"] = f"⚠️ AI service returned status {response.status_code}"
            except httpx.TimeoutException:
                status["ai_service"]["status"] = "timeout"
                status["ai_service"]["message"] = "⏱️ AI service request timed out"
            except httpx.ConnectError:
                status["ai_service"]["status"] = "unreachable"
                status["ai_service"]["message"] = "❌ AI service is unreachable"
    except Exception as e:
        status["ai_service"]["status"] = "error"
        status["ai_service"]["message"] = f"❌ AI service check failed: {str(e)}"
    
    return status

