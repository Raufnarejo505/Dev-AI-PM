from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_current_user
from app.models.alarm import Alarm
from app.schemas.alarm import AlarmRead, AlarmUpdate
from app.schemas.comment import CommentCreate, CommentRead
from app.services import alarm_service, comment_service
from app.models.user import User

router = APIRouter(prefix="/alarms", tags=["alarms"])


@router.get("", response_model=List[AlarmRead])
async def list_alarms(
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    query = select(Alarm).order_by(Alarm.created_at.desc())
    if status:
        # Map frontend status to backend status
        if status == "active":
            # Active means open or acknowledged
            query = query.where(Alarm.status.in_(["open", "acknowledged"]))
        else:
            query = query.where(Alarm.status == status)
    query = query.limit(200)
    result = await session.execute(query)
    return result.scalars().all()


@router.patch("/{alarm_id}", response_model=AlarmRead)
async def update_alarm(alarm_id: UUID, payload: AlarmUpdate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Alarm).where(Alarm.id == alarm_id))
    alarm = result.scalars().first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(alarm, field, value)
    await session.commit()
    await session.refresh(alarm)
    return alarm


@router.post("/{alarm_id}/resolve", response_model=AlarmRead)
async def resolve_alarm(
    alarm_id: UUID,
    resolution_notes: str = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Resolve an alarm with optional resolution notes"""
    result = await session.execute(select(Alarm).where(Alarm.id == alarm_id))
    alarm = result.scalars().first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
    
    resolved_alarm = await alarm_service.resolve_alarm(session, alarm, resolution_notes)
    
    # Log audit event
    from app.services import audit_service
    from app.schemas.audit_log import AuditLogCreate
    await audit_service.create_audit_log(
        session,
        AuditLogCreate(
            user_id=str(current_user.id),
            action_type="resolve",
            resource_type="alarm",
            resource_id=str(alarm_id),
            details=f"Alarm resolved: {resolution_notes or 'No notes provided'}",
            metadata={"resolution_notes": resolution_notes},
        ),
    )
    
    return resolved_alarm


@router.get("/prediction/{prediction_id}", response_model=List[AlarmRead])
async def get_alarms_by_prediction(prediction_id: UUID, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Alarm).where(Alarm.prediction_id == prediction_id))
    return result.scalars().all()


@router.post("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_update_alarms(payload: List[AlarmUpdate], ids: List[UUID], session: AsyncSession = Depends(get_session)):
    # This is a simplified bulk update, ideally we'd map updates to IDs
    # For now, let's assume we want to resolve multiple alarms
    for alarm_id in ids:
        result = await session.execute(select(Alarm).where(Alarm.id == alarm_id))
        alarm = result.scalars().first()
        if alarm:
            for field, value in payload[0].model_dump(exclude_unset=True).items():
                setattr(alarm, field, value)
    await session.commit()


@router.post("/{alarm_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def create_alarm_comment(
    alarm_id: UUID,
    payload: CommentCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Add a comment to an alarm"""
    # Verify alarm exists
    result = await session.execute(select(Alarm).where(Alarm.id == alarm_id))
    alarm = result.scalars().first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
    
    comment_data = CommentCreate(
        resource_type="alarm",
        resource_id=str(alarm_id),
        content=payload.content,
        is_internal=payload.is_internal,
    )
    return await comment_service.create_comment(session, comment_data, str(current_user.id))


@router.get("/{alarm_id}/comments", response_model=List[CommentRead])
async def get_alarm_comments(
    alarm_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get all comments for an alarm"""
    from app.services import comment_service
    
    # Verify alarm exists
    result = await session.execute(select(Alarm).where(Alarm.id == alarm_id))
    alarm = result.scalars().first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
    
    return await comment_service.get_comments(session, "alarm", str(alarm_id))

