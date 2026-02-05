from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.alarm import AlarmCreate
from app.services import alarm_service, ticket_service


@dataclass
class IncidentPolicy:
    early_wear_persist_seconds: int = 300
    advanced_wear_persist_seconds: int = 60
    fault_ticket_min_seconds: int = 180
    recovery_stable_seconds: int = 60


@dataclass
class MachineIncidentState:
    profile: int = 0
    profile_since: Optional[datetime] = None
    last_seen: Optional[datetime] = None


class IncidentManager:
    """Runtime incident controller.

    The goal is calmness:
    - Do not flap alarms.
    - Do not flood tickets.
    - One incident produces at most one alarm + one ticket.

    Persistence across restarts is achieved by using deterministic incident keys
    stored in Alarm/Ticket metadata and always re-checking DB before creating.
    """

    def __init__(self, policy: IncidentPolicy | None = None) -> None:
        self._policy = policy or IncidentPolicy()
        self._states: dict[str, MachineIncidentState] = {}

    def reset_runtime_state(self) -> None:
        self._states.clear()

    async def observe_profile(
        self,
        session: AsyncSession,
        *,
        machine_id: UUID,
        profile: int,
        observed_at: datetime,
    ) -> None:
        machine_key = str(machine_id)
        state = self._states.get(machine_key)
        if state is None:
            state = MachineIncidentState(profile=profile, profile_since=observed_at, last_seen=observed_at)
            self._states[machine_key] = state
        else:
            state.last_seen = observed_at
            if state.profile != profile:
                state.profile = profile
                state.profile_since = observed_at

        await self._apply_policy(session, machine_id=machine_id, state=state, now=observed_at)

    async def _apply_policy(
        self,
        session: AsyncSession,
        *,
        machine_id: UUID,
        state: MachineIncidentState,
        now: datetime,
    ) -> None:
        # Profile 0: baseline. No alarms/tickets must be generated.
        if state.profile == 0:
            if state.profile_since is None:
                return
            elapsed = (now - state.profile_since).total_seconds()
            if elapsed >= self._policy.recovery_stable_seconds:
                await self._resolve_incidents(session, machine_id=machine_id, now=now)
            return

        if state.profile_since is None:
            return

        elapsed = (now - state.profile_since).total_seconds()

        # Profile 1: one stable warning, no ticket.
        if state.profile == 1:
            if elapsed < self._policy.early_wear_persist_seconds:
                return
            incident_key = f"{machine_id}:profile1:early_wear"
            await self._ensure_alarm(
                session,
                machine_id=machine_id,
                incident_key=incident_key,
                severity="warning",
                message="Early wear detected (persistent trend)",
                triggered_at=state.profile_since,
                create_ticket=False,
            )
            return

        # Profile 2: exactly one critical alarm + one ticket. No repeats.
        if state.profile == 2:
            if elapsed < self._policy.advanced_wear_persist_seconds:
                return
            incident_key = f"{machine_id}:profile2:advanced_wear"
            await self._ensure_alarm(
                session,
                machine_id=machine_id,
                incident_key=incident_key,
                severity="critical",
                message="Advanced wear detected (controlled escalation)",
                triggered_at=state.profile_since,
                create_ticket=True,
                dedup_forever=True,
            )
            return

        # Profile 3: fault event.
        # Allow alarm while condition exists. Only ticket if fault is long.
        if state.profile == 3:
            incident_key = f"{machine_id}:profile3:fault_event"
            create_ticket = elapsed >= self._policy.fault_ticket_min_seconds
            await self._ensure_alarm(
                session,
                machine_id=machine_id,
                incident_key=incident_key,
                severity="critical",
                message="Fault event detected", 
                triggered_at=state.profile_since,
                create_ticket=create_ticket,
            )
            return

    async def _ensure_alarm(
        self,
        session: AsyncSession,
        *,
        machine_id: UUID,
        incident_key: str,
        severity: str,
        message: str,
        triggered_at: datetime,
        create_ticket: bool,
        dedup_forever: bool = False,
    ) -> None:
        if dedup_forever:
            existing = await alarm_service.get_alarm_by_incident_key(
                session,
                machine_id=machine_id,
                incident_key=incident_key,
            )
        else:
            existing = await alarm_service.get_active_alarm_by_incident_key(
                session,
                machine_id=machine_id,
                incident_key=incident_key,
            )
        if existing:
            return

        payload = AlarmCreate(
            machine_id=machine_id,
            sensor_id=None,
            prediction_id=None,
            severity=severity,
            message=message,
            triggered_at=triggered_at,
            metadata={
                "incident_key": incident_key,
            },
        )
        alarm = await alarm_service.create_alarm(session, payload)
        if create_ticket:
            await ticket_service.ensure_ticket_for_alarm(session, alarm)
        logger.warning("Incident alarm created: machine_id={}, key={}, severity={}", machine_id, incident_key, severity)

    async def _resolve_incidents(self, session: AsyncSession, *, machine_id: UUID, now: datetime) -> None:
        active_alarms = await alarm_service.list_active_incident_alarms(session, machine_id=machine_id)
        for alarm in active_alarms:
            await alarm_service.resolve_alarm(session, alarm, "Recovered to profile 0 (stable)")


incident_manager = IncidentManager()
