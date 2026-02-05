from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from functools import lru_cache
import time
import os
import re
import statistics

from fastapi import APIRouter, Depends, Query, HTTPException
from loguru import logger
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_current_user, require_viewer
from app.models.user import User
from app.models.machine import Machine
from app.models.sensor import Sensor
from app.models.prediction import Prediction
from app.models.alarm import Alarm
from app.models.sensor_data import SensorData

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


_extruder_last_attempt_at: datetime | None = None
_extruder_last_success_at: datetime | None = None
_extruder_last_error_at: datetime | None = None
_extruder_last_error: str | None = None

# Simple in-memory cache (can be replaced with Redis)
_cache: Dict[str, tuple] = {}
CACHE_TTL = 10  # seconds - reduced for faster alarm updates


def get_cached(key: str):
    """Get cached value if not expired"""
    if key in _cache:
        value, timestamp = _cache[key]
        if time.time() - timestamp < CACHE_TTL:
            return value
        del _cache[key]
    return None


def set_cached(key: str, value: Any):
    """Set cached value"""
    _cache[key] = (value, time.time())


@router.get("/overview")
async def get_overview(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_viewer),
):
    """Get dashboard overview statistics"""
    cache_key = "dashboard:overview"
    cached = get_cached(cache_key)
    if cached:
        return cached
    
    # Run all queries in parallel for better performance
    import asyncio
    
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    # Execute all queries concurrently using asyncio.gather
    machine_count, sensor_count, active_alarms, recent_predictions, machines_online = await asyncio.gather(
        session.scalar(select(func.count(Machine.id))),
        session.scalar(select(func.count(Sensor.id))),
        session.scalar(select(func.count(Alarm.id)).where(Alarm.status.in_(["open", "acknowledged"]))),
        session.scalar(select(func.count(Prediction.id)).where(Prediction.timestamp >= yesterday)),
        session.scalar(select(func.count(Machine.id)).where(Machine.status == "online")),
        return_exceptions=True
    )
    
    # Handle any exceptions
    machine_count = machine_count if not isinstance(machine_count, Exception) else 0
    sensor_count = sensor_count if not isinstance(sensor_count, Exception) else 0
    active_alarms = active_alarms if not isinstance(active_alarms, Exception) else 0
    recent_predictions = recent_predictions if not isinstance(recent_predictions, Exception) else 0
    machines_online = machines_online if not isinstance(machines_online, Exception) else 0
    
    result = {
        "machines": {
            "total": machine_count or 0,
            "online": machines_online or 0,
        },
        "sensors": {
            "total": sensor_count or 0,
        },
        "alarms": {
            "active": active_alarms or 0,
        },
        "predictions": {
            "last_24h": recent_predictions or 0,
        },
    }
    
    set_cached(cache_key, result)
    return result


@router.get("/extruder/latest")
async def get_extruder_latest_rows(
    current_user: User = Depends(require_viewer),
    limit: int = Query(200, ge=1, le=5000),
):
    global _extruder_last_attempt_at, _extruder_last_success_at, _extruder_last_error_at, _extruder_last_error
    _extruder_last_attempt_at = datetime.utcnow()

    host = (os.getenv("MSSQL_HOST") or "").strip()
    port_raw = (os.getenv("MSSQL_PORT") or "1433").strip()
    user = (os.getenv("MSSQL_USER") or "").strip()
    password = os.getenv("MSSQL_PASSWORD")
    database = (os.getenv("MSSQL_DATABASE") or "HISTORISCH").strip()
    table_raw = (os.getenv("MSSQL_TABLE") or "Tab_Actual").strip()
    schema_raw = (os.getenv("MSSQL_SCHEMA") or "dbo").strip()

    try:
        port = int(port_raw)
    except Exception:
        _extruder_last_error = "Invalid MSSQL_PORT"
        _extruder_last_error_at = datetime.utcnow()
        raise HTTPException(status_code=500, detail="Invalid MSSQL_PORT")

    if not host or not user or not password:
        _extruder_last_error = "MSSQL is not configured"
        _extruder_last_error_at = datetime.utcnow()
        raise HTTPException(status_code=500, detail="MSSQL is not configured")

    schema = schema_raw
    table = table_raw
    if "." in table_raw:
        parts = [p for p in table_raw.split(".") if p]
        if len(parts) != 2:
            _extruder_last_error = "Invalid MSSQL table identifier"
            _extruder_last_error_at = datetime.utcnow()
            raise HTTPException(status_code=500, detail="Invalid MSSQL table identifier")
        schema, table = parts[0], parts[1]

    if not re.fullmatch(r"[A-Za-z0-9_]+", schema or "") or not re.fullmatch(r"[A-Za-z0-9_]+", table or ""):
        _extruder_last_error = "Invalid MSSQL schema/table identifier"
        _extruder_last_error_at = datetime.utcnow()
        raise HTTPException(status_code=500, detail="Invalid MSSQL schema/table identifier")

    def _fetch_sync() -> Dict[str, Any]:
        import pymssql

        table_sql = f"[{schema}].[{table}]"
        # MSSQL 2000 does not support parentheses around TOP value
        query = (
            f"SELECT TOP {int(limit)} "
            f"TrendDate, "
            f"Val_4 AS ScrewSpeed_rpm, "
            f"Val_6 AS Pressure_bar, "
            f"Val_7 AS Temp_Zone1_C, "
            f"Val_8 AS Temp_Zone2_C, "
            f"Val_9 AS Temp_Zone3_C, "
            f"Val_10 AS Temp_Zone4_C "
            f"FROM {table_sql} "
            f"ORDER BY TrendDate DESC"
        )

        s = query.strip().lower()
        if not s.startswith("select") or ";" in s:
            raise ValueError("Unsafe SQL blocked")

        conn = pymssql.connect(
            server=host,
            user=user,
            password=password,
            database=database,
            port=port,
            login_timeout=10,
            timeout=10,
        )
        try:
            try:
                conn.autocommit(True)
            except Exception:
                pass

            cur = conn.cursor(as_dict=True)
            try:
                cur.execute("SET NOCOUNT ON")
                cur.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
            except Exception:
                pass

            cur.execute(query)
            rows = cur.fetchall() or []
            out = []
            for r in rows:
                td = r.get("TrendDate")
                if isinstance(td, datetime):
                    trend_date = td.isoformat()
                elif td is None:
                    trend_date = None
                else:
                    trend_date = str(td)

                out.append(
                    {
                        "TrendDate": trend_date,
                        "ScrewSpeed_rpm": r.get("ScrewSpeed_rpm"),
                        "Pressure_bar": r.get("Pressure_bar"),
                        "Temp_Zone1_C": r.get("Temp_Zone1_C"),
                        "Temp_Zone2_C": r.get("Temp_Zone2_C"),
                        "Temp_Zone3_C": r.get("Temp_Zone3_C"),
                        "Temp_Zone4_C": r.get("Temp_Zone4_C"),
                    }
                )

            out.reverse()
            return {"rows": out}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    try:
        import asyncio
        result = await asyncio.to_thread(_fetch_sync)
        _extruder_last_success_at = datetime.utcnow()
        _extruder_last_error = None
        _extruder_last_error_at = None
        return result
    except HTTPException:
        raise
    except Exception as e:
        msg = f"{type(e).__name__}: {e}"
        msg = msg.replace(password or "", "***")
        if len(msg) > 500:
            msg = msg[:500] + "..."

        logger.exception("MSSQL extruder read failed")
        _extruder_last_error = msg
        _extruder_last_error_at = datetime.utcnow()
        raise HTTPException(status_code=502, detail="Failed to read MSSQL extruder data")


@router.get("/extruder/status")
async def get_extruder_status(
    current_user: User = Depends(require_viewer),
):
    host = (os.getenv("MSSQL_HOST") or "").strip()
    port_raw = (os.getenv("MSSQL_PORT") or "1433").strip()
    user = (os.getenv("MSSQL_USER") or "").strip()
    password = os.getenv("MSSQL_PASSWORD")
    database = (os.getenv("MSSQL_DATABASE") or "HISTORISCH").strip()
    table_raw = (os.getenv("MSSQL_TABLE") or "Tab_Actual").strip()
    schema_raw = (os.getenv("MSSQL_SCHEMA") or "dbo").strip()

    schema = schema_raw
    table = table_raw
    if "." in table_raw:
        parts = [p for p in table_raw.split(".") if p]
        if len(parts) == 2:
            schema, table = parts[0], parts[1]

    configured = bool(host and user and password)
    try:
        port = int(port_raw)
    except Exception:
        port = None

    return {
        "configured": configured,
        "host": host or None,
        "port": port,
        "database": database or None,
        "schema": schema or None,
        "table": table or None,
        "last_attempt_at": _extruder_last_attempt_at.isoformat() if _extruder_last_attempt_at else None,
        "last_success_at": _extruder_last_success_at.isoformat() if _extruder_last_success_at else None,
        "last_error_at": _extruder_last_error_at.isoformat() if _extruder_last_error_at else None,
        "last_error": _extruder_last_error,
    }


@router.get("/extruder/derived")
async def get_extruder_derived_kpis(
    current_user: User = Depends(require_viewer),
    window_minutes: int = Query(30, ge=5, le=1440, description="Time window in minutes to analyze"),
) -> Dict[str, Any]:
    """
    Step 1–4: Read recent data, compute baseline, derived metrics, and risk indicators.
    Returns:
      - window_minutes: requested window
      - rows: raw rows in the window
      - baseline: per-sensor rolling baseline (mean) and normal range (mean ± 1 std)
      - derived: Temp_Avg, Temp_Spread, stability flags
      - risk: per-sensor risk level (green/yellow/red) and overall risk
    """
    import pymssql
    from datetime import datetime, timedelta

    global _extruder_last_attempt_at, _extruder_last_success_at, _extruder_last_error_at, _extruder_last_error
    _extruder_last_attempt_at = datetime.utcnow()

    # Load config from environment
    host = os.getenv("MSSQL_HOST")
    port_raw = os.getenv("MSSQL_PORT", "1433")
    user = os.getenv("MSSQL_USER")
    password = os.getenv("MSSQL_PASSWORD")
    database = (os.getenv("MSSQL_DATABASE") or "HISTORISCH").strip()
    table_raw = (os.getenv("MSSQL_TABLE") or "Tab_Actual").strip()
    schema_raw = (os.getenv("MSSQL_SCHEMA") or "dbo").strip()

    schema = schema_raw
    table = table_raw
    if "." in table_raw:
        parts = [p for p in table_raw.split(".") if p]
        if len(parts) == 2:
            schema, table = parts[0], parts[1]

    # Validate config
    try:
        port = int(port_raw)
    except Exception:
        _extruder_last_error_at = datetime.utcnow()
        _extruder_last_error = "Invalid MSSQL_PORT"
        raise HTTPException(status_code=500, detail="Invalid MSSQL_PORT")

    if not (host and user and password):
        _extruder_last_error_at = datetime.utcnow()
        _extruder_last_error = "Missing MSSQL connection config"
        raise HTTPException(status_code=500, detail="Missing MSSQL connection config")

    # Step 1: Read latest data within time window
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
    conn = None
    try:
        conn = pymssql.connect(
            server=host,
            port=port,
            user=user,
            password=password,
            database=database,
            as_dict=True,
            login_timeout=10,
        )
        cursor = conn.cursor()
        # Use SQL 2000 compatible syntax
        sql = f"""
        SELECT TOP 200
            TrendDate,
            Val_4 AS ScrewSpeed_rpm,
            Val_6 AS Pressure_bar,
            Val_7 AS Temp_Zone1_C,
            Val_8 AS Temp_Zone2_C,
            Val_9 AS Temp_Zone3_C,
            Val_10 AS Temp_Zone4_C
        FROM [{schema}].[{table}]
        WHERE TrendDate >= DATEADD(minute, -{window_minutes}, GETDATE())
        ORDER BY TrendDate DESC
        """
        cursor.execute(sql)
        rows_raw = cursor.fetchall()
        # Ensure TrendDate is datetime
        rows = []
        for r in rows_raw:
            td = r.get("TrendDate")
            if isinstance(td, datetime):
                rows.append(r)
        # Reverse to chronological order (oldest first)
        rows = list(reversed(rows))
        _extruder_last_success_at = datetime.utcnow()
        _extruder_last_error = None
        _extruder_last_error_at = None
    except Exception as e:
        _extruder_last_error_at = datetime.utcnow()
        _extruder_last_error = str(e)
        logger.error(f"MSSQL extruder/derived error: {e}")
        raise HTTPException(status_code=502, detail=f"MSSQL error: {e}")
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass

    if not rows:
        return {
            "window_minutes": window_minutes,
            "rows": [],
            "baseline": {},
            "derived": {},
            "risk": {"overall": "unknown", "sensors": {}},
        }

    # Helper to extract numeric values safely
    def as_float(val):
        try:
            return float(val) if val is not None else None
        except Exception:
            return None

    # Step 2: Baseline calculation per sensor, operating-point aware
    sensor_keys = ["ScrewSpeed_rpm", "Pressure_bar", "Temp_Zone1_C", "Temp_Zone2_C", "Temp_Zone3_C", "Temp_Zone4_C"]
    baseline = {}
    # Determine operating point by ScrewSpeed_rpm buckets (simple 2-rpm bins)
    screw_speeds = [as_float(r.get("ScrewSpeed_rpm")) for r in rows if as_float(r.get("ScrewSpeed_rpm")) is not None]
    if screw_speeds:
        current_speed = screw_speeds[-1]
        # Create bucket: round to nearest 2 rpm
        speed_bucket = round(current_speed / 2) * 2
        # Filter rows within this operating point (±2 rpm)
        op_rows = [r for r in rows if as_float(r.get("ScrewSpeed_rpm")) is not None and abs(as_float(r.get("ScrewSpeed_rpm")) - speed_bucket) <= 2]
    else:
        op_rows = rows

    for key in sensor_keys:
        values = [as_float(r.get(key)) for r in op_rows if as_float(r.get(key)) is not None]
        if values:
            mean_val = statistics.mean(values)
            std_val = statistics.stdev(values) if len(values) > 1 else 0.0
            baseline[key] = {
                "mean": round(mean_val, 3),
                "std": round(std_val, 3),
                "min_normal": round(mean_val - std_val, 3),
                "max_normal": round(mean_val + std_val, 3),
                "count": len(values),
                "op_bucket": speed_bucket if key == "ScrewSpeed_rpm" else None,
            }
        else:
            baseline[key] = {"mean": None, "std": None, "min_normal": None, "max_normal": None, "count": 0, "op_bucket": None}

    # Step 3: Derived metrics
    derived = {}
    # Temperature averages per row
    temp_keys = ["Temp_Zone1_C", "Temp_Zone2_C", "Temp_Zone3_C", "Temp_Zone4_C"]
    for r in rows:
        temps = [as_float(r.get(k)) for k in temp_keys if as_float(r.get(k)) is not None]
        if temps:
            r["Temp_Avg"] = round(statistics.mean(temps), 3)
            r["Temp_Spread"] = round(max(temps) - min(temps), 3)
        else:
            r["Temp_Avg"] = None
            r["Temp_Spread"] = None
    # Overall derived aggregates
    all_temp_avg = [r["Temp_Avg"] for r in rows if r.get("Temp_Avg") is not None]
    all_temp_spread = [r["Temp_Spread"] for r in rows if r.get("Temp_Spread") is not None]
    derived["Temp_Avg"] = {
        "current": rows[-1].get("Temp_Avg") if rows else None,
        "mean": round(statistics.mean(all_temp_avg), 3) if all_temp_avg else None,
        "std": round(statistics.stdev(all_temp_avg), 3) if len(all_temp_avg) > 1 else None,
    }
    derived["Temp_Spread"] = {
        "current": rows[-1].get("Temp_Spread") if rows else None,
        "mean": round(statistics.mean(all_temp_spread), 3) if all_temp_spread else None,
        "std": round(statistics.stdev(all_temp_spread), 3) if len(all_temp_spread) > 1 else None,
    }
    # Stability indicators: % of points within normal range
    stability = {}
    for key in sensor_keys:
        vals = [as_float(r.get(key)) for r in rows if as_float(r.get(key)) is not None]
        base = baseline.get(key, {})
        min_n = base.get("min_normal")
        max_n = base.get("max_normal")
        if min_n is not None and max_n is not None and vals:
            stable_count = sum(1 for v in vals if min_n <= v <= max_n)
            stability[key] = round(100 * stable_count / len(vals), 1)
        else:
            stability[key] = None
    derived["stability_percent"] = stability

    # Per-sensor time spread (stability) within window
    per_sensor_spread = {}
    for key in sensor_keys:
        vals = [as_float(r.get(key)) for r in rows if as_float(r.get(key)) is not None]
        if len(vals) >= 2:
            spread = max(vals) - min(vals)
            per_sensor_spread[key] = round(spread, 3)
        else:
            per_sensor_spread[key] = None
    derived["per_sensor_spread"] = per_sensor_spread

    # Step 4: Risk logic (green/yellow/red) per sensor
    def risk_level(value, baseline):
        if value is None or baseline.get("mean") is None:
            return "unknown"
        mean = baseline["mean"]
        std = baseline.get("std", 0)
        if std == 0:
            return "green"
        # Z-score based thresholds
        z = abs(value - mean) / std
        if z <= 1:
            return "green"
        elif z <= 2:
            return "yellow"
        else:
            return "red"

    risk_sensors = {}
    current_row = rows[-1] if rows else {}
    for key in sensor_keys:
        val = as_float(current_row.get(key))
        risk_sensors[key] = risk_level(val, baseline.get(key, {}))
    # Overall risk: worst sensor risk
    risk_order = {"green": 0, "yellow": 1, "red": 2, "unknown": -1}
    overall_risk = max(risk_sensors.values(), key=lambda x: risk_order.get(x, -1)) if risk_sensors else "unknown"

    # Explanations per sensor
    explanations = {}
    for key in sensor_keys:
        val = as_float(current_row.get(key))
        base = baseline.get(key, {})
        mean = base.get("mean")
        std = base.get("std")
        risk = risk_sensors.get(key)
        if risk == "red":
            explanations[key] = f"{key} critically deviates from normal ({mean:.1f}±{std:.1f})"
        elif risk == "yellow":
            explanations[key] = f"{key} drifting from normal ({mean:.1f}±{std:.1f})"
        elif risk == "green":
            explanations[key] = f"{key} stable"
        else:
            explanations[key] = f"{key} unknown"
    derived["explanations"] = explanations

    return {
        "window_minutes": window_minutes,
        "rows": rows,
        "baseline": baseline,
        "derived": derived,
        "risk": {"overall": overall_risk, "sensors": risk_sensors},
    }


@router.get("/machines/stats")
async def get_machines_stats(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_viewer),
):
    """Get machine statistics"""
    cache_key = "dashboard:machines:stats"
    cached = get_cached(cache_key)
    if cached:
        return cached
    
    # Count by status
    status_counts = {}
    for status in ["online", "offline", "maintenance", "degraded"]:
        count = await session.scalar(
            select(func.count(Machine.id)).where(Machine.status == status)
        )
        status_counts[status] = count or 0
    
    # Count by criticality
    criticality_counts = {}
    for crit in ["low", "medium", "high", "critical"]:
        count = await session.scalar(
            select(func.count(Machine.id)).where(Machine.criticality == crit)
        )
        criticality_counts[crit] = count or 0
    
    result = {
        "by_status": status_counts,
        "by_criticality": criticality_counts,
    }
    
    set_cached(cache_key, result)
    return result


@router.get("/sensors/stats")
async def get_sensors_stats(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_viewer),
):
    """Get sensor statistics"""
    cache_key = "dashboard:sensors:stats"
    cached = get_cached(cache_key)
    if cached:
        return cached
    
    total = await session.scalar(select(func.count(Sensor.id)))
    
    # Count by type (if type is stored)
    # This is a simplified version - adjust based on your sensor type field
    
    result = {
        "total": total or 0,
    }
    
    set_cached(cache_key, result)
    return result


@router.get("/predictions/stats")
async def get_predictions_stats(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_viewer),
    hours: int = Query(24, ge=1, le=168),
):
    """Get prediction statistics for the last N hours"""
    cache_key = f"dashboard:predictions:stats:{hours}"
    cached = get_cached(cache_key)
    if cached:
        return cached
    
    since = datetime.utcnow() - timedelta(hours=hours)
    
    total = await session.scalar(
        select(func.count(Prediction.id)).where(Prediction.created_at >= since)
    )
    
    # Count by status
    status_counts = {}
    for status in ["normal", "warning", "critical"]:
        count = await session.scalar(
            select(func.count(Prediction.id)).where(
                and_(
                    Prediction.timestamp >= since,
                    Prediction.status == status
                )
            )
        )
        status_counts[status] = count or 0
    
    result = {
        "total": total or 0,
        "by_status": status_counts,
        "period_hours": hours,
    }
    
    set_cached(cache_key, result)
    return result


