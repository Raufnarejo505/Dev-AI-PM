import httpx
from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_current_user, require_admin, require_engineer, require_viewer
from app.core.config import get_settings
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["ai"])

settings = get_settings()


@router.get("/status")
async def get_ai_status(
    session: AsyncSession = Depends(get_session),
    # Any authenticated user (viewer/engineer/admin) can see AI status
    current_user: User = Depends(require_viewer),
):
    """Get AI service status and health"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ai_service_url}/health")
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "unhealthy",
                    "error": f"AI service returned {response.status_code}",
                }
    except Exception as e:
        return {
            "status": "unreachable",
            "error": str(e),
        }


@router.post("/retrain")
async def trigger_retrain(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Trigger AI model retraining (stub - queues retrain job)"""
    # This is a stub implementation
    # In production, this would queue a retrain job
    job_id = f"retrain_{datetime.utcnow().isoformat()}"
    
    # Log the retrain request
    from app.services import audit_service
    from app.schemas.audit_log import AuditLogCreate
    await audit_service.create_audit_log(
        session,
        AuditLogCreate(
            user_id=str(current_user.id),
            action_type="retrain",
            resource_type="ai_model",
            details=f"Retrain job queued: {job_id}",
        ),
    )
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Retrain job has been queued. This is a stub implementation.",
    }


@router.get("/logs")
async def get_ai_logs(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_engineer),
    limit: int = 100,
):
    """Get AI service logs (stub - returns recent audit logs related to AI)"""
    from app.services import audit_service
    
    logs = await audit_service.get_audit_logs(
        session,
        resource_type="ai_model",
        limit=limit,
    )
    
    return [
        {
            "timestamp": log.created_at.isoformat(),
            "action": log.action_type,
            "details": log.details,
            "metadata": log.metadata_json,
        }
        for log in logs
    ]


@router.get("/models")
async def list_models(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_engineer),
):
    """List all AI model versions"""
    from app.models.model_registry import ModelRegistry
    from sqlalchemy import select
    
    result = await session.execute(select(ModelRegistry).order_by(ModelRegistry.created_at.desc()))
    models = result.scalars().all()
    
    return [
        {
            "id": str(model.id),
            "name": model.name,
            "version": model.version,
            "description": model.description,
            "path": model.path,
            "metadata": model.metadata_json,
            "created_at": model.created_at.isoformat(),
        }
        for model in models
    ]


@router.post("/models")
async def register_model(
    name: str,
    version: str,
    description: str = None,
    path: str = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Register a new AI model version (admin only)"""
    from app.models.model_registry import ModelRegistry
    
    model = ModelRegistry(
        name=name,
        version=version,
        description=description,
        path=path,
    )
    session.add(model)
    await session.commit()
    await session.refresh(model)
    
    return {
        "id": str(model.id),
        "name": model.name,
        "version": model.version,
        "message": "Model registered successfully",
    }


@router.post("/models/{version}/activate")
async def activate_model(
    version: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Activate/promote a model version to production (admin only)"""
    # This is a stub - in production, this would update AI service configuration
    # For now, we just log it
    
    from app.services import audit_service
    from app.schemas.audit_log import AuditLogCreate
    
    await audit_service.create_audit_log(
        session,
        AuditLogCreate(
            user_id=str(current_user.id),
            action_type="model_activate",
            resource_type="ai_model",
            resource_id=version,
            details=f"Model version {version} activated",
        ),
    )
    
    return {
        "version": version,
        "status": "activated",
        "message": f"Model version {version} has been activated (stub implementation)",
    }


@router.post("/models/{version}/rollback")
async def rollback_model(
    version: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Rollback to a previous model version (admin only)"""
    from app.services import audit_service
    from app.schemas.audit_log import AuditLogCreate
    
    await audit_service.create_audit_log(
        session,
        AuditLogCreate(
            user_id=str(current_user.id),
            action_type="model_rollback",
            resource_type="ai_model",
            resource_id=version,
            details=f"Rolled back to model version {version}",
        ),
    )
    
    return {
        "version": version,
        "status": "rolled_back",
        "message": f"Rolled back to model version {version} (stub implementation)",
    }

