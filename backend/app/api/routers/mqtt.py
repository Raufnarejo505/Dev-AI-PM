from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_current_user
from app.core.config import get_settings
from app.mqtt.consumer import mqtt_ingestor
from app.models.user import User

router = APIRouter(prefix="/mqtt", tags=["mqtt"])

settings = get_settings()


@router.get("/status")
async def get_mqtt_status(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get MQTT broker and consumer status"""
    client = mqtt_ingestor.client
    is_connected = False
    
    if client:
        try:
            # Check connection status
            is_connected = client.is_connected()
            # Also check if client has valid socket connection
            if hasattr(client, '_sock') and client._sock:
                is_connected = True
        except Exception:
            is_connected = False
    
    # Get queue size safely
    queue_size = 0
    try:
        if mqtt_ingestor.queue:
            queue_size = mqtt_ingestor.queue.qsize()
    except Exception:
        queue_size = 0
    
    return {
        "connected": is_connected,
        "broker": {
            "host": settings.mqtt_broker_host,
            "port": settings.mqtt_broker_port,
        },
        "consumer": {
            "connected": is_connected,
            "topics": settings.mqtt_topics,
            "queue_size": queue_size,
        },
    }
