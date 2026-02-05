import asyncio
import json
from typing import Dict, Any, Set, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Request, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from jose import JWTError, jwt

from app.api.dependencies import get_session
from app.core.config import get_settings
from app.models.user import User
from app.models.sensor_data import SensorData
from app.models.prediction import Prediction
from app.models.alarm import Alarm
from app.services import user_service

settings = get_settings()

router = APIRouter(prefix="/ws", tags=["realtime"])

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# Global event queue for SSE (stores last 100 events) - initialized lazily
_event_queue: asyncio.Queue = None
event_listeners: Set[int] = set()  # Track SSE connections

def get_event_queue():
    """Get or create the global event queue"""
    global _event_queue
    if _event_queue is None:
        _event_queue = asyncio.Queue(maxsize=100)
    return _event_queue


@router.websocket("/updates")
async def websocket_updates(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    connection_id = f"conn_{datetime.now(timezone.utc).timestamp()}"
    active_connections[connection_id] = websocket
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "connection_id": connection_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        # Keep connection alive and send updates
        while True:
            # Wait for client message (ping/pong)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Echo back or handle client messages
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
    except WebSocketDisconnect:
        pass
    finally:
        active_connections.pop(connection_id, None)


async def broadcast_update(update_type: str, data: Dict[str, Any]):
    """Broadcast update to all connected WebSocket clients and SSE listeners"""
    message = {
        "type": update_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # Send to WebSocket connections
    disconnected = []
    for conn_id, websocket in active_connections.items():
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected.append(conn_id)
    for conn_id in disconnected:
        active_connections.pop(conn_id, None)
    
    # Add to event queue for SSE
    try:
        queue = get_event_queue()
        queue.put_nowait(message)
    except asyncio.QueueFull:
        # Remove oldest event if queue is full
        try:
            queue.get_nowait()
            queue.put_nowait(message)
        except asyncio.QueueEmpty:
            pass


@router.get("/events/stream")
async def server_sent_events(
    request: Request,
    session: AsyncSession = Depends(get_session),
    token: Optional[str] = Query(None),
):
    """Server-Sent Events endpoint for one-way real-time updates"""
    
    # Authenticate user - SSE can't use headers, so we use query param or Authorization header
    current_user = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide token as query parameter '?token=...' or Authorization header",
        )
    
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        current_user = await user_service.get_user_by_email(session, email)
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    async def event_generator():
        listener_id = id(event_generator)
        event_listeners.add(listener_id)
        last_count = {"sensor_data": 0, "predictions": 0, "alarms": 0}
        last_db_check = datetime.now(timezone.utc)
        last_heartbeat = datetime.now(timezone.utc)
        
        try:
            while True:
                try:
                    # Process all events in queue first (real-time priority)
                    queue = get_event_queue()
                    events_processed = 0
                    while events_processed < 10:  # Process up to 10 events per loop
                        try:
                            event = queue.get_nowait()
                            yield f"data: {json.dumps(event)}\n\n"
                            events_processed += 1
                            # Update counts if it's a prediction or alarm event
                            if event.get("type") == "prediction.created":
                                last_count["predictions"] += 1
                            elif event.get("type") == "alarm.created":
                                last_count["alarms"] += 1
                            elif event.get("type") == "alarm.updated":
                                # Alarm resolved, might need to update count
                                pass
                        except asyncio.QueueEmpty:
                            break
                    
                    # Only check database periodically (every 5 seconds) to reduce load
                    now = datetime.now(timezone.utc)
                    if (now - last_db_check).total_seconds() >= 5.0:
                        from sqlalchemy import func
                        prediction_count_result = await session.execute(
                            select(func.count(Prediction.id))
                        )
                        prediction_count = prediction_count_result.scalar() or 0
                        
                        alarm_count_result = await session.execute(
                            select(func.count(Alarm.id)).where(Alarm.status == "active")
                        )
                        alarm_count = alarm_count_result.scalar() or 0
                        
                        # Send update if counts changed significantly
                        if (abs(prediction_count - last_count["predictions"]) > 0 or
                            abs(alarm_count - last_count["alarms"]) > 0):
                            
                            update_data = {
                                'type': 'update',
                                'predictions_count': prediction_count,
                                'active_alarms': alarm_count,
                                'timestamp': now.isoformat(),
                            }
                            yield f"data: {json.dumps(update_data)}\n\n"
                            
                            last_count = {
                                "predictions": prediction_count,
                                "alarms": alarm_count,
                            }
                        
                        last_db_check = now
                    
                    # Send heartbeat every 30 seconds
                    if (now - last_heartbeat).total_seconds() >= 30.0:
                        heartbeat_data = {
                            'type': 'heartbeat',
                            'timestamp': now.isoformat(),
                        }
                        yield f"data: {json.dumps(heartbeat_data)}\n\n"
                        last_heartbeat = now
                    
                    # Short sleep for rapid queue checking, longer if no events
                    await asyncio.sleep(0.5 if events_processed > 0 else 1.0)
                
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    error_data = {
                        'type': 'error',
                        'message': str(e),
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    await asyncio.sleep(2)
        finally:
            event_listeners.discard(listener_id)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

