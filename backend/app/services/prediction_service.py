from datetime import datetime
from typing import Any, Dict, List

import httpx
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionCreate, PredictionRequest

settings = get_settings()


def _prepare_payload(data: dict) -> dict:
    metadata = data.pop("metadata", None)
    if metadata is not None:
        data["metadata_json"] = metadata
    # Map remaining_useful_life to rul (model column name)
    if "remaining_useful_life" in data:
        data["rul"] = data.pop("remaining_useful_life")
    return data


async def call_ai_service(payload: PredictionRequest) -> Dict[str, Any]:
    ai_request = {
        "sensor_id": str(payload.sensor_id),
        "machine_id": str(payload.machine_id),
        "timestamp": payload.timestamp.isoformat(),
        "readings": payload.context.get("readings")
        if payload.context and "readings" in payload.context
        else {"value": payload.value},
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(f"{settings.ai_service_url}/predict", json=ai_request)
        response.raise_for_status()
        return response.json()


async def persist_prediction(session: AsyncSession, payload: PredictionCreate) -> Prediction:
    data = payload.model_dump()
    # Ensure score is set if not provided (use confidence or default)
    if data.get("score") is None:
        data["score"] = data.get("confidence", 0.0) or 0.0
    prediction = Prediction(**_prepare_payload(data))
    session.add(prediction)
    await session.commit()
    await session.refresh(prediction)
    
    # Broadcast real-time update
    try:
        from app.api.routers.realtime import broadcast_update
        await broadcast_update(
            "prediction.created",
            {
                "id": str(prediction.id),
                "machine_id": str(prediction.machine_id),
                "sensor_id": str(prediction.sensor_id),
                "status": prediction.status or "normal",
                "prediction": prediction.prediction or "normal",
                "score": float(prediction.score) if prediction.score else 0.0,
                "confidence": float(prediction.confidence) if prediction.confidence else 0.0,
                "timestamp": prediction.timestamp.isoformat() if prediction.timestamp else None,
                "anomaly_type": prediction.anomaly_type,
            }
        )
    except Exception as e:
        logger.debug(f"Failed to broadcast prediction update: {e}")
    
    return prediction


async def run_prediction_workflow(session: AsyncSession, payload: PredictionRequest) -> Prediction:
    ai_result = await call_ai_service(payload)
    logger.info("AI service responded {}", ai_result)

    # Map AI service response: prediction, status, score, confidence, anomaly_type, model_version, rul
    prediction_payload = PredictionCreate(
        sensor_id=payload.sensor_id,
        machine_id=payload.machine_id,
        timestamp=payload.timestamp,
        prediction=ai_result.get("prediction", "normal"),
        status=ai_result.get("status", "normal"),
        score=float(ai_result.get("score", 0.0)),
        confidence=float(ai_result.get("confidence", 0.0)),
        anomaly_type=ai_result.get("anomaly_type"),
        model_version=ai_result.get("model_version", "unknown"),
        remaining_useful_life=ai_result.get("rul"),
        response_time_ms=float(ai_result.get("response_time_ms", 0.0)),
        contributing_features=ai_result.get("contributing_features"),
        metadata=ai_result,
    )
    return await persist_prediction(session, prediction_payload)


async def create_prediction(session: AsyncSession, payload: PredictionCreate) -> Prediction:
    return await persist_prediction(session, payload)


async def get_history(
    session: AsyncSession,
    machine_id: str,
    start_time: datetime = None,
    end_time: datetime = None,
    limit: int = 100,
) -> List[Prediction]:
    from sqlalchemy import select
    stmt = select(Prediction).where(Prediction.machine_id == machine_id)
    
    if start_time:
        stmt = stmt.where(Prediction.timestamp >= start_time)
    if end_time:
        stmt = stmt.where(Prediction.timestamp <= end_time)
        
    stmt = stmt.order_by(Prediction.timestamp.desc()).limit(limit)
    
    result = await session.execute(stmt)
    return list(reversed(result.scalars().all()))

