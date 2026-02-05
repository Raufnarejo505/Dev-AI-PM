from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_current_user, require_admin, require_engineer
from app.models.user import User
from app.models.job import Job
from app.schemas.job import JobCreate, JobRead, JobUpdate

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=List[JobRead])
async def list_jobs(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_engineer),
    job_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
):
    """List background jobs"""
    query = select(Job)
    if job_type:
        query = query.where(Job.job_type == job_type)
    if status:
        query = query.where(Job.status == status)
    query = query.order_by(Job.created_at.desc()).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_engineer),
):
    """Get job status"""
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Create/enqueue a new background job (admin only)"""
    job = Job(
        job_type=payload.job_type,
        status="pending",
        created_by=str(current_user.id),
        metadata_json=payload.metadata,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    
    # In production, this would enqueue the job to a task queue (Celery, RQ, etc.)
    # For now, it's just stored in the database
    
    return job


@router.post("/{job_id}/retry", response_model=JobRead)
async def retry_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Retry a failed job (admin only)"""
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "failed":
        raise HTTPException(status_code=400, detail="Job is not in failed state")
    
    job.status = "pending"
    job.error_message = None
    await session.commit()
    await session.refresh(job)
    
    return job

