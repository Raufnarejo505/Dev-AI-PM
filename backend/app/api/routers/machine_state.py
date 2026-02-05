"""
API router for machine state management and configuration
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import get_current_user, get_session
from app.models.user import User
from app.models.machine import Machine
from app.schemas.machine_state import (
    MachineStateInfo, MachineStateThresholds, MachineStateThresholdsCreate,
    MachineStateThresholdsUpdate, MachineStateTransition, MachineStateAlert,
    MachineProcessEvaluation, MachineStateHistory, MachineStateStatistics,
    MachineStateBulkResponse, ProcessEvaluationRequest, ProcessEvaluationResponse,
    TrafficLightStatus, MachineStateConfigRequest, MachineStateConfigResponse
)
from app.services.machine_state_manager import MachineStateService
from app.services.machine_state_service import get_machine_detector, get_all_machine_states

router = APIRouter(prefix="/machine-state", tags=["machine-state"])


@router.get("/states/current", response_model=Dict[str, MachineStateInfo])
async def get_all_current_states(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Get current states of all machines"""
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        state_service = MachineStateService(db)
        states = await state_service.get_all_current_states()
        
        logger.info("API: Retrieved {} machine states", len(states))
        for machine_id, state_info in states.items():
            logger.info("API: machine_id={}, state={}, confidence={:.2f}", 
                       machine_id, state_info.state.value, state_info.confidence)
        
        # Convert to response format
        response = {}
        for machine_id, state_info in states.items():
            response[machine_id] = MachineStateInfo(
                machine_id=state_info.machine_id,
                state=state_info.state,
                confidence=state_info.confidence,
                state_since=state_info.state_since,
                last_updated=state_info.last_updated,
                metrics=state_info.metrics,
                flags=state_info.flags,
                state_duration_seconds=state_info.state_duration_seconds
            )
        
        return response
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error("API error getting machine states: {}", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get machine states: {str(e)}")


@router.get("/states/{machine_id}/current", response_model=MachineStateInfo)
async def get_machine_current_state(
    machine_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Get current state of a specific machine"""
    try:
        state_service = MachineStateService(db)
        state_info = await state_service.get_current_state(machine_id)
        
        if not state_info:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        return MachineStateInfo(
            machine_id=state_info.machine_id,
            state=state_info.state,
            confidence=state_info.confidence,
            state_since=state_info.state_since,
            last_updated=state_info.last_updated,
            metrics=state_info.metrics,
            flags=state_info.flags,
            state_duration_seconds=state_info.state_duration_seconds
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get machine state: {str(e)}")


@router.get("/states/{machine_id}/history", response_model=List[MachineStateTransition])
async def get_machine_state_history(
    machine_id: str,
    start_time: Optional[datetime] = Query(None, description="Start time for history"),
    end_time: Optional[datetime] = Query(None, description="End time for history"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of transitions"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Get state transition history for a machine"""
    try:
        # Verify machine exists
        machine_result = await db.execute(
            select(Machine).where(Machine.name == machine_id)
        )
        machine = machine_result.scalar_one_or_none()
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        state_service = MachineStateService(db)
        transitions = await state_service.get_state_history(
            machine_id, start_time, end_time, limit
        )
        
        return transitions
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get state history: {str(e)}")


@router.get("/states/{machine_id}/statistics", response_model=MachineStateStatistics)
async def get_machine_state_statistics(
    machine_id: str,
    start_time: datetime = Query(..., description="Start time for statistics"),
    end_time: datetime = Query(..., description="End time for statistics"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Get state statistics for a machine over time period"""
    try:
        # Verify machine exists
        machine_result = await db.execute(
            select(Machine).where(Machine.name == machine_id)
        )
        machine = machine_result.scalar_one_or_none()
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        # Validate time range
        if end_time <= start_time:
            raise HTTPException(status_code=400, detail="End time must be after start time")
        
        if (end_time - start_time) > timedelta(days=90):
            raise HTTPException(status_code=400, detail="Time range cannot exceed 90 days")
        
        state_service = MachineStateService(db)
        statistics = await state_service.get_state_statistics(machine_id, start_time, end_time)
        
        return statistics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get state statistics: {str(e)}")


# Thresholds Management
@router.get("/thresholds/{machine_id}", response_model=MachineStateThresholds)
async def get_machine_thresholds(
    machine_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Get state detection thresholds for a machine"""
    try:
        # Verify machine exists
        machine_result = await db.execute(
            select(Machine).where(Machine.name == machine_id)
        )
        machine = machine_result.scalar_one_or_none()
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        state_service = MachineStateService(db)
        thresholds = await state_service.get_machine_thresholds(machine_id)
        
        if not thresholds:
            # Return default thresholds
            return MachineStateThresholds(machine_id=machine_id)
        
        return MachineStateThresholds.from_orm(thresholds)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get thresholds: {str(e)}")


@router.post("/thresholds/{machine_id}", response_model=MachineStateThresholds)
async def create_machine_thresholds(
    machine_id: str,
    thresholds: MachineStateThresholdsCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Create or update state detection thresholds for a machine"""
    try:
        # Check permissions - need Engineer or Admin role
        if current_user.role not in ["admin", "engineer"]:
            raise HTTPException(status_code=403, detail="Admin or Engineer role required")
        
        # Verify machine exists
        machine_result = await db.execute(
            select(Machine).where(Machine.name == machine_id)
        )
        machine = machine_result.scalar_one_or_none()
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        state_service = MachineStateService(db)
        db_thresholds = await state_service.create_machine_thresholds(
            machine_id, thresholds, created_by=current_user.email
        )
        
        return MachineStateThresholds.from_orm(db_thresholds)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create thresholds: {str(e)}")


@router.put("/thresholds/{machine_id}", response_model=MachineStateThresholds)
async def update_machine_thresholds(
    machine_id: str,
    thresholds_update: MachineStateThresholdsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Update state detection thresholds for a machine"""
    try:
        # Check permissions - need Engineer or Admin role
        if current_user.role not in ["admin", "engineer"]:
            raise HTTPException(status_code=403, detail="Admin or Engineer role required")
        
        # Verify machine exists
        machine_result = await db.execute(
            select(Machine).where(Machine.name == machine_id)
        )
        machine = machine_result.scalar_one_or_none()
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        # Get existing thresholds
        state_service = MachineStateService(db)
        existing = await state_service.get_machine_thresholds(machine_id)
        
        if not existing:
            raise HTTPException(status_code=404, detail=f"Thresholds not found for machine {machine_id}")
        
        # Update thresholds
        update_data = thresholds_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(existing, field):
                setattr(existing, field, value)
        
        existing.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing)
        
        # Reinitialize detector with new thresholds
        await state_service.initialize_machine_detector(machine_id)
        
        return MachineStateThresholds.from_orm(existing)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update thresholds: {str(e)}")


@router.delete("/thresholds/{machine_id}")
async def delete_machine_thresholds(
    machine_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Delete state detection thresholds for a machine"""
    try:
        # Check permissions - need Admin role
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin role required")
        
        # Verify machine exists
        machine_result = await db.execute(
            select(Machine).where(Machine.name == machine_id)
        )
        machine = machine_result.scalar_one_or_none()
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        # Delete thresholds
        from app.models.machine_state import MachineStateThresholds
        thresholds_result = await db.execute(
            select(MachineStateThresholds).where(MachineStateThresholds.machine_id == machine_id)
        )
        thresholds = thresholds_result.scalar_one_or_none()
        
        if thresholds:
            await db.delete(thresholds)
            await db.commit()
        
        # Cleanup detector
        await state_service.cleanup_detector(machine_id)
        
        return {"message": f"Thresholds deleted for machine {machine_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete thresholds: {str(e)}")


# Process Evaluation
@router.post("/evaluate/{machine_id}", response_model=ProcessEvaluationResponse)
async def trigger_process_evaluation(
    machine_id: str,
    request: ProcessEvaluationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Trigger process evaluation for a machine (only works in PRODUCTION state)"""
    try:
        # Check permissions - need Engineer or Admin role
        if current_user.role not in ["admin", "engineer"]:
            raise HTTPException(status_code=403, detail="Admin or Engineer role required")
        
        # Verify machine exists
        machine_result = await db.execute(
            select(Machine).where(Machine.name == machine_id)
        )
        machine = machine_result.scalar_one_or_none()
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        # Get current state
        state_service = MachineStateService(db)
        current_state = await state_service.get_current_state(machine_id)
        
        if not current_state:
            return ProcessEvaluationResponse(
                machine_id=machine_id,
                evaluation_performed=False,
                message="Machine state not available",
                evaluation_time=datetime.utcnow()
            )
        
        # Check if machine is in PRODUCTION state (unless forced)
        if current_state.state.value != "PRODUCTION" and not request.force_evaluation:
            return ProcessEvaluationResponse(
                machine_id=machine_id,
                evaluation_performed=False,
                message=f"Machine is in {current_state.state.value} state. Process evaluation only runs in PRODUCTION state.",
                evaluation_time=datetime.utcnow()
            )
        
        # Trigger process evaluation in background
        background_tasks.add_task(
            _run_process_evaluation,
            db,
            machine_id,
            current_state,
            request.force_evaluation
        )
        
        return ProcessEvaluationResponse(
            machine_id=machine_id,
            evaluation_performed=True,
            message="Process evaluation triggered",
            evaluation_time=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger process evaluation: {str(e)}")


@router.get("/evaluations/{machine_id}", response_model=List[MachineProcessEvaluation])
async def get_process_evaluations(
    machine_id: str,
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of evaluations"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Get process evaluation history for a machine"""
    try:
        # Verify machine exists
        machine_result = await db.execute(
            select(Machine).where(Machine.name == machine_id)
        )
        machine = machine_result.scalar_one_or_none()
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        # Query process evaluations
        from app.models.machine_state import MachineProcessEvaluation
        query = select(MachineProcessEvaluation).where(
            MachineProcessEvaluation.machine_id == machine.id
        )
        
        if start_time:
            query = query.where(MachineProcessEvaluation.evaluation_time >= start_time)
        if end_time:
            query = query.where(MachineProcessEvaluation.evaluation_time <= end_time)
        
        query = query.order_by(MachineProcessEvaluation.evaluation_time.desc()).limit(limit)
        
        result = await db.execute(query)
        evaluations = result.scalars().all()
        
        return [MachineProcessEvaluation.from_orm(eval) for eval in evaluations]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get process evaluations: {str(e)}")


@router.get("/alerts/{machine_id}", response_model=List[MachineStateAlert])
async def get_machine_state_alerts(
    machine_id: str,
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of alerts"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Get state alerts for a machine"""
    try:
        # Verify machine exists
        machine_result = await db.execute(
            select(Machine).where(Machine.name == machine_id)
        )
        machine = machine_result.scalar_one_or_none()
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        # Query alerts
        from app.models.machine_state import MachineStateAlert
        query = select(MachineStateAlert).where(
            MachineStateAlert.machine_id == machine.id
        )
        
        if start_time:
            query = query.where(MachineStateAlert.alert_time >= start_time)
        if end_time:
            query = query.where(MachineStateAlert.alert_time <= end_time)
        if severity:
            query = query.where(MachineStateAlert.severity == severity)
        if acknowledged is not None:
            query = query.where(MachineStateAlert.is_acknowledged == acknowledged)
        
        query = query.order_by(MachineStateAlert.alert_time.desc()).limit(limit)
        
        result = await db.execute(query)
        alerts = result.scalars().all()
        
        return [MachineStateAlert.from_orm(alert) for alert in alerts]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


async def _run_process_evaluation(
    db: AsyncSession,
    machine_id: str,
    current_state,
    force_evaluation: bool
):
    """Background task to run process evaluation"""
    try:
        # This would integrate with the AI service for process evaluation
        # Implementation depends on AI service capabilities
        logger.info(f"Running process evaluation for {machine_id}")
        
    except Exception as e:
        logger.error(f"Process evaluation failed for {machine_id}: {e}")
