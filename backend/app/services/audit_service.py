from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate


async def create_audit_log(
    session: AsyncSession,
    audit_data: AuditLogCreate,
) -> AuditLog:
    """Create an audit log entry"""
    audit_log = AuditLog(**audit_data.model_dump())
    session.add(audit_log)
    await session.commit()
    await session.refresh(audit_log)
    return audit_log


async def get_audit_logs(
    session: AsyncSession,
    user_id: Optional[str] = None,
    action_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[AuditLog]:
    """Get audit logs with filtering"""
    query = select(AuditLog)
    
    conditions = []
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if action_type:
        conditions.append(AuditLog.action_type == action_type)
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    if resource_id:
        conditions.append(AuditLog.resource_id == resource_id)
    if start_date:
        conditions.append(AuditLog.created_at >= start_date)
    if end_date:
        conditions.append(AuditLog.created_at <= end_date)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(query)
    return list(result.scalars().all())

