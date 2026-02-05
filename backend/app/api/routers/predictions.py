from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_current_user
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.prediction import PredictionRead, PredictionRequest
from app.services import prediction_service, sensor_data_service

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("", response_model=PredictionRead, status_code=status.HTTP_201_CREATED)
async def run_prediction(payload: PredictionRequest, session: AsyncSession = Depends(get_session)):
    return await prediction_service.run_prediction_workflow(session, payload)


@router.get("", response_model=List[PredictionRead])
async def list_predictions(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    limit: int = Query(200, ge=1, le=1000),
    sort: str = Query("desc", regex="^(asc|desc)$"),
):
    from sqlalchemy import asc, desc
    order_by = desc(Prediction.timestamp) if sort == "desc" else asc(Prediction.timestamp)
    result = await session.execute(select(Prediction).order_by(order_by).limit(limit))
    predictions = result.scalars().all()
    
    # Ensure proper serialization
    return [
        PredictionRead.model_validate({
            "id": str(p.id),
            "sensor_id": str(p.sensor_id),
            "machine_id": str(p.machine_id),
            "timestamp": p.timestamp,
            "score": float(p.score) if p.score else 0.0,
            "status": p.status or "normal",
            "prediction": p.prediction or p.status or "normal",
            "confidence": float(p.confidence) if p.confidence else float(p.score) if p.score else 0.0,
            "anomaly_type": p.anomaly_type,
            "model_version": p.model_version,
            "remaining_useful_life": p.rul,
            "response_time_ms": float(p.response_time_ms) if p.response_time_ms else None,
            "contributing_features": p.contributing_features,
            "metadata": p.metadata_json or {},
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        })
        for p in predictions
    ]


@router.get("/{prediction_id}/explain")
async def explain_prediction(
    prediction_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get prediction explanation with feature importance"""
    prediction = await session.get(Prediction, prediction_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    # Extract explanation from metadata
    metadata = prediction.metadata_json or {}
    
    return {
        "prediction_id": str(prediction_id),
        "explanation": {
            "predicted_class": prediction.prediction,
            "confidence": float(prediction.confidence) if prediction.confidence else None,
            "feature_importance": metadata.get("contributing_features", {}),
            "model_version": prediction.model_version,
            "reasoning": metadata.get("reasoning", "Based on sensor data patterns"),
            "recommended_action": metadata.get("recommended_action"),
        },
        "metadata": metadata,
    }