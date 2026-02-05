from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Deque, Dict, Optional, Tuple

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.machine import Machine
from app.schemas.alarm import AlarmCreate
from app.services import alarm_service, ticket_service


# Canonical variables used across ingestion/AI/storage.
CANONICAL_VARS = {
    "temperature",
    "motor_current",
    "pressure",
    "vibration",
}


@dataclass
class OperatingRanges:
    # These ranges are used ONLY for AI reasoning (no direct hard alarm generation).
    temperature_normal: Tuple[float, float] = (180.0, 220.0)
    temperature_warning: Tuple[float, float] = (225.0, 240.0)
    temperature_fault: Tuple[float, float] = (160.0, 245.0)  # fault if <160 or >245

    motor_current_normal: Tuple[float, float] = (18.0, 30.0)
    motor_current_warning: Tuple[float, float] = (30.0, 36.0)
    motor_current_fault_hi: float = 38.0

    pressure_normal: Tuple[float, float] = (80.0, 140.0)
    pressure_warning: Tuple[float, float] = (145.0, 170.0)
    pressure_fault_hi: float = 180.0

    vibration_normal: Tuple[float, float] = (0.5, 2.0)
    vibration_warning: Tuple[float, float] = (2.1, 4.0)
    vibration_fault_hi: float = 4.5

    wear_index_normal: Tuple[float, float] = (0.0, 0.3)
    wear_index_degrading: Tuple[float, float] = (0.4, 0.7)
    wear_index_fault_hi: float = 0.8


@dataclass
class Decision:
    profile: str  # "A" | "B" | "C"
    severity: str  # "normal" | "warning" | "critical"
    confidence: float
    reason: str
    wear_index: float
    evidence: Dict[str, float]


class _MachineWindow:
    def __init__(self) -> None:
        self.series: Dict[str, Deque[Tuple[datetime, float]]] = {
            "temperature": deque(),
            "motor_current": deque(),
            "pressure": deque(),
            "vibration": deque(),
        }
        self.wear_index: float = 0.0
        self.last_eval_at: Optional[datetime] = None


class ExtruderAIDecisionService:
    """Production-grade, conservative profile logic for extruder machines.

    Key properties:
    - Trend-based (sliding window), not snapshot-based.
    - Calm: alarms and tickets are created only on profile transitions and with cooldown.
    - Backward compatible: uses existing Alarm/Ticket tables via metadata fields.

    Machine state persistence:
    - Active profile and calm-control timestamps are stored in Machine.metadata_json["ai_state"].
    """

    WINDOW_MINUTES = 10
    MIN_WINDOW_MINUTES_FOR_TRENDS = 5
    EVAL_THROTTLE_SECONDS = 20  # avoid recomputing on every sensor point

    ALARM_COOLDOWN_MINUTES = 15

    # Slope thresholds are deliberately conservative.
    # Units are per minute.
    SLOPE_THRESHOLDS = {
        "motor_current": 0.20,  # A/min
        "pressure": 1.00,  # bar/min
        "vibration": 0.05,  # mm/s per min
    }

    # Wear index behavior
    WEAR_INCREASE_RATE = 0.004  # per minute at high stress
    WEAR_DECAY_RATE = 0.0015  # per minute when stable

    def __init__(self, ranges: Optional[OperatingRanges] = None) -> None:
        self._ranges = ranges or OperatingRanges()
        self._windows: Dict[str, _MachineWindow] = {}

    def _get_window(self, machine_id: str) -> _MachineWindow:
        w = self._windows.get(machine_id)
        if w is None:
            w = _MachineWindow()
            self._windows[machine_id] = w
        return w

    @staticmethod
    def _utc(ts: datetime) -> datetime:
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)

    def observe(self, *, machine_id: str, var_name: str, value: float, timestamp: datetime) -> None:
        """Observe one canonical variable value for a machine."""
        if var_name not in CANONICAL_VARS:
            return

        w = self._get_window(machine_id)
        ts = self._utc(timestamp)
        w.series[var_name].append((ts, float(value)))
        self._trim(w, now=ts)

    def _trim(self, w: _MachineWindow, *, now: datetime) -> None:
        cutoff = now - timedelta(minutes=self.WINDOW_MINUTES)
        for dq in w.series.values():
            while dq and dq[0][0] < cutoff:
                dq.popleft()

    @staticmethod
    def _slope_per_minute(points: Deque[Tuple[datetime, float]]) -> Optional[float]:
        if len(points) < 3:
            return None

        t0 = points[0][0]
        xs = []
        ys = []
        for ts, v in points:
            dt_min = (ts - t0).total_seconds() / 60.0
            xs.append(dt_min)
            ys.append(v)

        x_mean = sum(xs) / len(xs)
        y_mean = sum(ys) / len(ys)
        denom = sum((x - x_mean) ** 2 for x in xs)
        if denom <= 1e-9:
            return None
        numer = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
        return numer / denom

    @staticmethod
    def _latest(points: Deque[Tuple[datetime, float]]) -> Optional[float]:
        return float(points[-1][1]) if points else None

    def _fault_breach(self, *, temperature: Optional[float], motor_current: Optional[float], pressure: Optional[float], vibration: Optional[float]) -> bool:
        r = self._ranges

        if temperature is not None:
            if temperature > r.temperature_fault[1] or temperature < r.temperature_fault[0]:
                return True

        if motor_current is not None:
            if motor_current > r.motor_current_fault_hi:
                return True

        if pressure is not None:
            if pressure > r.pressure_fault_hi:
                return True

        if vibration is not None:
            if vibration > r.vibration_fault_hi:
                return True

        return False

    @staticmethod
    def _clamp01(x: float) -> float:
        return max(0.0, min(1.0, x))

    def _normalized_stress(self, *, motor_current: Optional[float], pressure: Optional[float], vibration: Optional[float]) -> float:
        """Normalize stress into 0..1 using warning/fault bands (conservative)."""
        r = self._ranges

        def norm(v: Optional[float], warn_lo: float, warn_hi: float, fault_hi: float) -> float:
            if v is None:
                return 0.0
            if v <= warn_lo:
                return 0.0
            if v >= fault_hi:
                return 1.0
            # map warn_lo..fault_hi linearly
            return (v - warn_lo) / max(1e-6, (fault_hi - warn_lo))

        s_mc = norm(motor_current, r.motor_current_warning[0], r.motor_current_warning[1], r.motor_current_fault_hi)
        s_p = norm(pressure, r.pressure_warning[0], r.pressure_warning[1], r.pressure_fault_hi)
        s_v = norm(vibration, r.vibration_warning[0], r.vibration_warning[1], r.vibration_fault_hi)
        return self._clamp01((s_mc + s_p + s_v) / 3.0)

    def _update_wear_index(self, *, current: float, stress: float, dt_minutes: float) -> float:
        # Increase slowly under stress, decay slowly when stable.
        inc = self.WEAR_INCREASE_RATE * stress * dt_minutes
        dec = self.WEAR_DECAY_RATE * (1.0 - stress) * dt_minutes
        return self._clamp01(current + inc - dec)

    def decide(self, *, machine_id: str, now: datetime) -> Optional[Decision]:
        w = self._get_window(machine_id)
        now = self._utc(now)

        # Throttle decisions to avoid heavy work on every ingestion.
        if w.last_eval_at is not None and (now - w.last_eval_at).total_seconds() < self.EVAL_THROTTLE_SECONDS:
            return None
        w.last_eval_at = now

        temperature = self._latest(w.series["temperature"])
        motor_current = self._latest(w.series["motor_current"])
        pressure = self._latest(w.series["pressure"])
        vibration = self._latest(w.series["vibration"])

        # Require at least a minimum window for trend-based escalation.
        oldest_ts = None
        for dq in w.series.values():
            if dq:
                oldest_ts = dq[0][0] if oldest_ts is None else min(oldest_ts, dq[0][0])
        window_minutes = (now - oldest_ts).total_seconds() / 60.0 if oldest_ts else 0.0

        slope_mc = self._slope_per_minute(w.series["motor_current"]) or 0.0
        slope_p = self._slope_per_minute(w.series["pressure"]) or 0.0
        slope_v = self._slope_per_minute(w.series["vibration"]) or 0.0

        fault = self._fault_breach(
            temperature=temperature,
            motor_current=motor_current,
            pressure=pressure,
            vibration=vibration,
        )

        # Wear index: uses stress + time (monotonic-ish, no abrupt resets).
        stress = self._normalized_stress(motor_current=motor_current, pressure=pressure, vibration=vibration)
        dt_minutes = 1.0
        if oldest_ts is not None and w.series["pressure"]:
            # Use last two points of any available variable to estimate dt (fallback 1 minute).
            dq_any = next((dq for dq in w.series.values() if len(dq) >= 2), None)
            if dq_any:
                dt_minutes = max(0.1, (dq_any[-1][0] - dq_any[-2][0]).total_seconds() / 60.0)

        w.wear_index = self._update_wear_index(current=w.wear_index, stress=stress, dt_minutes=dt_minutes)

        evidence = {
            "window_minutes": round(window_minutes, 2),
            "slope_motor_current_per_min": round(slope_mc, 4),
            "slope_pressure_per_min": round(slope_p, 4),
            "slope_vibration_per_min": round(slope_v, 4),
            "stress": round(stress, 4),
            "wear_index": round(w.wear_index, 4),
        }

        # Default: Profile A (normal)
        profile = "A"
        severity = "normal"
        confidence = 0.75
        reason = "Stable operation within expected behaviour"

        # Profile C (fault) criteria: fault breach OR strong multi-parameter persistent trend.
        trending_abnormal = 0
        if slope_mc >= self.SLOPE_THRESHOLDS["motor_current"]:
            trending_abnormal += 1
        if slope_p >= self.SLOPE_THRESHOLDS["pressure"]:
            trending_abnormal += 1
        if slope_v >= self.SLOPE_THRESHOLDS["vibration"]:
            trending_abnormal += 1

        if fault:
            profile = "C"
            severity = "critical"
            confidence = 0.92
            reason = "Fault threshold breach detected (AI reasoning ranges)"
        elif window_minutes >= self.MIN_WINDOW_MINUTES_FOR_TRENDS and trending_abnormal >= 3:
            profile = "C"
            severity = "critical"
            confidence = 0.88
            reason = "Strong correlated abnormal trends across motor current, pressure and vibration"
        # Profile B (degradation) criteria: gradual drift in any two of MC/Pressure/Vibration, sustained.
        elif window_minutes >= self.MIN_WINDOW_MINUTES_FOR_TRENDS and trending_abnormal >= 2:
            profile = "B"
            severity = "warning"
            confidence = 0.70
            reason = "Degradation/drift: sustained upward trends in at least two key variables"

        # WearIndex itself can also push confidence (but should not escalate aggressively).
        if profile != "C" and w.wear_index >= self._ranges.wear_index_degrading[0]:
            confidence = max(confidence, 0.72)
            evidence["wear_index_flag"] = 1.0

        # Conservative: do not escalate based on short windows.
        # IMPORTANT: fault breaches must be allowed to escalate immediately.
        # We only buffer (downgrade to Profile A) when escalation is purely trend-based.
        if window_minutes < self.MIN_WINDOW_MINUTES_FOR_TRENDS and profile in {"B", "C"} and not fault:
            return Decision(
                profile="A",
                severity="normal",
                confidence=0.65,
                reason="Insufficient history for trend-based escalation (buffering)",
                wear_index=w.wear_index,
                evidence=evidence,
            )

        return Decision(
            profile=profile,
            severity=severity,
            confidence=confidence,
            reason=reason,
            wear_index=w.wear_index,
            evidence=evidence,
        )

    @staticmethod
    def _get_ai_state(machine: Machine) -> dict:
        md = machine.metadata_json or {}
        ai_state = md.get("ai_state")
        if not isinstance(ai_state, dict):
            ai_state = {}
        return ai_state

    @staticmethod
    def _set_ai_state(machine: Machine, ai_state: dict) -> None:
        md = machine.metadata_json or {}
        md["ai_state"] = ai_state
        machine.metadata_json = md

    @staticmethod
    def _parse_dt(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    async def apply_and_maybe_raise_incident(
        self,
        session: AsyncSession,
        *,
        machine: Machine,
        observed_at: datetime,
        decision: Decision,
    ) -> None:
        """Persist profile state to machine metadata and (calmly) create alarms/tickets."""
        observed_at = self._utc(observed_at)

        ai_state = self._get_ai_state(machine)
        prev_profile = str(ai_state.get("active_profile") or "A")

        # Update machine-level AI state for dashboard.
        ai_state["active_profile"] = decision.profile
        ai_state["severity"] = decision.severity
        ai_state["confidence"] = float(decision.confidence)
        ai_state["wear_index"] = float(round(decision.wear_index, 4))
        ai_state["reason"] = decision.reason
        ai_state["updated_at"] = observed_at.isoformat()

        # Calm control timestamps
        last_warning_alarm_at = self._parse_dt(ai_state.get("last_warning_alarm_at"))
        last_fault_alarm_at = self._parse_dt(ai_state.get("last_fault_alarm_at"))
        last_profile_c_ticket_at = self._parse_dt(ai_state.get("last_profile_c_ticket_at"))

        # Always persist state (no deletions of history).
        self._set_ai_state(machine, ai_state)
        session.add(machine)
        await session.commit()

        # Suppress duplicate alarms if status unchanged.
        if decision.profile == prev_profile:
            return

        cooldown = timedelta(minutes=self.ALARM_COOLDOWN_MINUTES)

        # Profile A: on recovery, resolve active incident alarms (optional calmness).
        if decision.profile == "A":
            try:
                await self._resolve_extruder_incidents(session, machine_id=machine.id, now=observed_at)
            except Exception as e:
                logger.debug(f"Failed to resolve extruder incidents: {e}")
            return

        if decision.profile == "B":
            if last_warning_alarm_at and (observed_at - last_warning_alarm_at) < cooldown:
                return

            incident_key = f"{machine.id}:extruder:profileB"
            alarm = await alarm_service.create_alarm(
                session,
                AlarmCreate(
                    machine_id=machine.id,
                    sensor_id=None,
                    prediction_id=None,
                    severity="warning",
                    message="Extruder degradation detected (trend-based)",
                    triggered_at=observed_at,
                    metadata={
                        "incident_key": incident_key,
                        "ai_profile": "B",
                        "confidence": float(decision.confidence),
                        "wear_index": float(decision.wear_index),
                        "reason": decision.reason,
                        "evidence": decision.evidence,
                    },
                ),
            )
            logger.warning("Extruder WARNING alarm created: alarm_id={}, machine_id={}", alarm.id, machine.id)

            ai_state["last_warning_alarm_at"] = observed_at.isoformat()
            self._set_ai_state(machine, ai_state)
            session.add(machine)
            await session.commit()
            return

        if decision.profile == "C":
            if last_fault_alarm_at and (observed_at - last_fault_alarm_at) < cooldown:
                return

            incident_key = f"{machine.id}:extruder:profileC"
            alarm = await alarm_service.create_alarm(
                session,
                AlarmCreate(
                    machine_id=machine.id,
                    sensor_id=None,
                    prediction_id=None,
                    severity="critical",
                    message="Extruder fault detected (trend-based)",
                    triggered_at=observed_at,
                    metadata={
                        "incident_key": incident_key,
                        "ai_profile": "C",
                        "confidence": float(decision.confidence),
                        "wear_index": float(decision.wear_index),
                        "reason": decision.reason,
                        "evidence": decision.evidence,
                    },
                ),
            )

            # Tickets can only be created on transition to Profile C.
            # Also avoid repeated tickets if a previous Profile C ticket was created recently.
            if not last_profile_c_ticket_at or (observed_at - last_profile_c_ticket_at) >= cooldown:
                await ticket_service.ensure_ticket_for_alarm(session, alarm)
                ai_state["last_profile_c_ticket_at"] = observed_at.isoformat()

            ai_state["last_fault_alarm_at"] = observed_at.isoformat()
            self._set_ai_state(machine, ai_state)
            session.add(machine)
            await session.commit()
            return

    async def _resolve_extruder_incidents(self, session: AsyncSession, *, machine_id, now: datetime) -> None:
        # Resolve only incident alarms created by this service.
        active_alarms = await alarm_service.list_active_incident_alarms(session, machine_id=machine_id)
        for alarm in active_alarms:
            incident_key = (alarm.metadata_json or {}).get("incident_key", "")
            if ":extruder:" in incident_key:
                await alarm_service.resolve_alarm(session, alarm, "Recovered to Profile A (stable)")


extruder_ai_service = ExtruderAIDecisionService()
