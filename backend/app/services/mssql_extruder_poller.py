import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.schemas.machine import MachineCreate
from app.schemas.prediction import PredictionCreate, PredictionRequest
from app.schemas.sensor import SensorCreate
from app.services import machine_service, prediction_service, sensor_service
from app.services import settings_service


@dataclass
class ExtruderSqlRow:
    trend_date: datetime
    screw_speed_rpm: float
    pressure_bar: float
    temp_zone1_c: float
    temp_zone2_c: float
    temp_zone3_c: float
    temp_zone4_c: float


class MSSQLExtruderPoller:
    def __init__(
        self,
        *,
        enabled: bool,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        table: str,
        poll_interval_seconds: int,
        window_minutes: int,
        max_rows_per_poll: int,
        machine_name: str,
        sensor_name: str,
    ) -> None:
        self.enabled = enabled
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.table = table
        self.poll_interval_seconds = poll_interval_seconds
        self.window_minutes = window_minutes
        self.max_rows_per_poll = max_rows_per_poll
        self.machine_name = machine_name
        self.sensor_name = sensor_name

        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()
        self._last_trend_date: Optional[datetime] = None
        self._window: List[ExtruderSqlRow] = []

        self._machine_id = None
        self._sensor_id = None

        self._config_last_loaded_at: Optional[datetime] = None
        self._config_reload_seconds: int = 30
        self._effective_enabled: bool = False
        self._config_fingerprint: Optional[str] = None

        self._consecutive_failures: int = 0
        self._next_retry_at: Optional[datetime] = None
        self._max_backoff_seconds: int = 300

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        if not self.enabled:
            logger.info("MSSQL extruder poller master-disabled (MSSQL_ENABLED=false). Poller will not start.")
            return
        if self._task and not self._task.done():
            return
        self._stop.clear()
        self._task = loop.create_task(self._run())
        logger.info("MSSQL extruder poller started")

    async def stop(self) -> None:
        if not self._task:
            return
        self._stop.set()
        try:
            await asyncio.wait_for(self._task, timeout=10)
        except Exception:
            pass

    @staticmethod
    def _safe_float(v: Any) -> float:
        try:
            if v is None:
                return 0.0
            return float(v)
        except Exception:
            return 0.0

    def _trim_window(self) -> None:
        if not self._window:
            return
        cutoff = self._window[-1].trend_date - timedelta(minutes=self.window_minutes)
        self._window = [r for r in self._window if r.trend_date >= cutoff]

    def _compute_features(self) -> Tuple[Dict[str, float], Dict[str, Any]]:
        rows = self._window
        if len(rows) < 2:
            latest = rows[-1] if rows else None
            readings = {
                "rpm": float(latest.screw_speed_rpm) if latest else 0.0,
                "pressure": float(latest.pressure_bar) if latest else 0.0,
                "temperature": float(
                    np.mean([
                        latest.temp_zone1_c,
                        latest.temp_zone2_c,
                        latest.temp_zone3_c,
                        latest.temp_zone4_c,
                    ])
                )
                if latest
                else 0.0,
            }
            meta = {
                "window_size": len(rows),
                "window_minutes": self.window_minutes,
                "features": {},
            }
            return readings, meta

        arr = {
            "rpm": np.array([r.screw_speed_rpm for r in rows], dtype=np.float64),
            "pressure": np.array([r.pressure_bar for r in rows], dtype=np.float64),
            "tz1": np.array([r.temp_zone1_c for r in rows], dtype=np.float64),
            "tz2": np.array([r.temp_zone2_c for r in rows], dtype=np.float64),
            "tz3": np.array([r.temp_zone3_c for r in rows], dtype=np.float64),
            "tz4": np.array([r.temp_zone4_c for r in rows], dtype=np.float64),
        }
        temp_avg = (arr["tz1"] + arr["tz2"] + arr["tz3"] + arr["tz4"]) / 4.0

        def stats(x: np.ndarray, prefix: str) -> Dict[str, float]:
            x = np.asarray(x, dtype=np.float64)
            if len(x) == 0:
                return {}
            return {
                f"{prefix}_ma": float(np.mean(x)),
                f"{prefix}_std": float(np.std(x)),
                f"{prefix}_delta": float(x[-1] - x[-2]) if len(x) >= 2 else 0.0,
                f"{prefix}_delta_from_ma": float(x[-1] - float(np.mean(x))),
            }

        features: Dict[str, float] = {}
        features.update(stats(arr["rpm"], "rpm"))
        features.update(stats(arr["pressure"], "pressure"))
        features.update(stats(temp_avg, "temp_avg"))
        features.update(stats(arr["tz1"], "temp_zone1"))
        features.update(stats(arr["tz2"], "temp_zone2"))
        features.update(stats(arr["tz3"], "temp_zone3"))
        features.update(stats(arr["tz4"], "temp_zone4"))

        def corr(a: np.ndarray, b: np.ndarray) -> float:
            if len(a) < 3 or len(b) < 3:
                return 0.0
            try:
                c = float(np.corrcoef(a, b)[0, 1])
                if np.isnan(c) or np.isinf(c):
                    return 0.0
                return c
            except Exception:
                return 0.0

        features["corr_pressure_rpm"] = corr(arr["pressure"], arr["rpm"])
        features["corr_tempavg_rpm"] = corr(temp_avg, arr["rpm"])

        latest = rows[-1]
        readings = {
            "rpm": float(latest.screw_speed_rpm),
            "pressure": float(latest.pressure_bar),
            "temperature": float(np.mean([latest.temp_zone1_c, latest.temp_zone2_c, latest.temp_zone3_c, latest.temp_zone4_c])),
            "temp_zone1": float(latest.temp_zone1_c),
            "temp_zone2": float(latest.temp_zone2_c),
            "temp_zone3": float(latest.temp_zone3_c),
            "temp_zone4": float(latest.temp_zone4_c),
            "pressure_delta": float(features.get("pressure_delta", 0.0)),
            "rpm_delta": float(features.get("rpm_delta", 0.0)),
            "temp_avg_delta": float(features.get("temp_avg_delta", 0.0)),
            "corr_pressure_rpm": float(features.get("corr_pressure_rpm", 0.0)),
        }

        drift_score = float(
            min(
                1.0,
                (
                    abs(features.get("pressure_delta_from_ma", 0.0)) / 50.0
                    + abs(features.get("temp_avg_delta_from_ma", 0.0)) / 20.0
                )
                / 2.0,
            )
        )

        meta = {
            "window_size": len(rows),
            "window_minutes": self.window_minutes,
            "features": features,
            "drift_score": drift_score,
        }
        return readings, meta

    async def _ensure_machine_and_sensor(self) -> None:
        async with AsyncSessionLocal() as session:
            machine = await machine_service.get_machine(session, self.machine_name)
            if machine is None:
                machine = await machine_service.create_machine(
                    session,
                    MachineCreate(
                        name=self.machine_name,
                        status="online",
                        criticality="high",
                        metadata={
                            "source": "mssql",
                            "mssql_database": self.database,
                            "mssql_table": self.table,
                        },
                    ),
                )

            sensor = await sensor_service.get_sensor(session, self.sensor_name)
            if sensor is None:
                sensor = await sensor_service.create_sensor(
                    session,
                    SensorCreate(
                        machine_id=machine.id,
                        name=self.sensor_name,
                        sensor_type="extruder_sql",
                        unit=None,
                        metadata={
                            "source": "mssql",
                            "columns": ["Val_4", "Val_6", "Val_7", "Val_8", "Val_9", "Val_10"],
                            "trend_column": "TrendDate",
                        },
                    ),
                )

            self._machine_id = machine.id
            self._sensor_id = sensor.id

    async def _load_runtime_config(self) -> None:
        now = datetime.utcnow()
        if self._config_last_loaded_at and (now - self._config_last_loaded_at).total_seconds() < self._config_reload_seconds:
            return

        cfg_from_db: Dict[str, Any] = {}
        async with AsyncSessionLocal() as session:
            setting = await settings_service.get_setting(session, "connections.mssql")
            if setting and setting.value:
                try:
                    cfg_from_db = json.loads(setting.value) or {}
                except Exception:
                    cfg_from_db = {}

        merged = {
            "enabled": bool(cfg_from_db.get("enabled", False)),
            "host": str(cfg_from_db.get("host") or self.host or ""),
            "port": int(cfg_from_db.get("port") or self.port or 1433),
            "username": str(cfg_from_db.get("username") or self.username or ""),
            "password": cfg_from_db.get("password") or self.password or "",
            "database": str(cfg_from_db.get("database") or self.database or "HISTORISCH"),
            "table": str(cfg_from_db.get("table") or self.table or "Tab_Actual"),
            "poll_interval_seconds": int(cfg_from_db.get("poll_interval_seconds") or self.poll_interval_seconds or 60),
            "window_minutes": int(cfg_from_db.get("window_minutes") or self.window_minutes or 10),
            "max_rows_per_poll": int(cfg_from_db.get("max_rows_per_poll") or self.max_rows_per_poll or 5000),
        }

        # DB-stored password may be masked by a UI read, but PUT endpoint should store real password.
        if merged.get("password") == "********":
            merged["password"] = self.password or ""

        # Master enable comes from env; effective enable comes from DB toggle.
        effective_enabled = bool(merged.get("enabled"))

        fingerprint = json.dumps(merged, sort_keys=True)
        if self._config_fingerprint != fingerprint:
            self.host = merged["host"]
            self.port = merged["port"]
            self.username = merged["username"]
            self.password = merged["password"]
            self.database = merged["database"]
            self.table = merged["table"]
            self.poll_interval_seconds = merged["poll_interval_seconds"]
            self.window_minutes = merged["window_minutes"]
            self.max_rows_per_poll = merged["max_rows_per_poll"]

            # Reset the window if the data source or window size changes.
            self._window = []
            self._last_trend_date = None

            self._config_fingerprint = fingerprint
            logger.info("MSSQL extruder poller config reloaded from DB")

        self._effective_enabled = effective_enabled
        self._config_last_loaded_at = now

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=20))
    def _fetch_rows_sync(self) -> List[ExtruderSqlRow]:
        import pymssql

        # Prevent injection or accidental multi-statement execution via config.
        # Allow only simple identifiers like Tab_Actual.
        if not re.fullmatch(r"[A-Za-z0-9_]+", self.table or ""):
            raise ValueError("Invalid MSSQL table identifier")

        table_sql = f"[dbo].[{self.table}]"

        def _ensure_select_only(sql: str) -> None:
            s = (sql or "").strip().lower()
            if not s.startswith("select"):
                raise ValueError("Non-SELECT statement blocked")
            blocked = (
                "insert ",
                "update ",
                "delete ",
                "merge ",
                "alter ",
                "drop ",
                "create ",
                "truncate ",
                "exec ",
                "execute ",
                ";",
            )
            if any(tok in s for tok in blocked):
                raise ValueError("Potentially unsafe SQL blocked")

        conn = pymssql.connect(
            server=self.host,
            user=self.username,
            password=self.password,
            database=self.database,
            port=self.port,
            login_timeout=10,
            timeout=10,
        )
        try:
            # Make the connection read-friendly.
            try:
                conn.autocommit(True)
            except Exception:
                pass

            cur = conn.cursor(as_dict=True)
            try:
                cur.execute("SET NOCOUNT ON")
                cur.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
            except Exception:
                # Not critical; continue.
                pass

            if self._last_trend_date is None:
                query = (
                    f"SELECT TOP ({self.max_rows_per_poll}) TrendDate, Val_4, Val_6, Val_7, Val_8, Val_9, Val_10 "
                    f"FROM {table_sql} "
                    f"WHERE TrendDate >= DATEADD(minute, -{int(self.window_minutes)}, GETDATE()) "
                    f"ORDER BY TrendDate ASC"
                )
                _ensure_select_only(query)
                cur.execute(query)
            else:
                query = (
                    f"SELECT TOP ({self.max_rows_per_poll}) TrendDate, Val_4, Val_6, Val_7, Val_8, Val_9, Val_10 "
                    f"FROM {table_sql} "
                    f"WHERE TrendDate > %s "
                    f"ORDER BY TrendDate ASC"
                )
                _ensure_select_only(query)
                cur.execute(query, (self._last_trend_date,))

            rows = cur.fetchall() or []
            out: List[ExtruderSqlRow] = []
            for r in rows:
                td = r.get("TrendDate")
                if not isinstance(td, datetime):
                    continue
                out.append(
                    ExtruderSqlRow(
                        trend_date=td,
                        screw_speed_rpm=self._safe_float(r.get("Val_4")),
                        pressure_bar=self._safe_float(r.get("Val_6")),
                        temp_zone1_c=self._safe_float(r.get("Val_7")),
                        temp_zone2_c=self._safe_float(r.get("Val_8")),
                        temp_zone3_c=self._safe_float(r.get("Val_9")),
                        temp_zone4_c=self._safe_float(r.get("Val_10")),
                    )
                )
            return out
        finally:
            try:
                conn.close()
            except Exception:
                pass

    async def _persist_prediction(self, *, ts: datetime, ai_result: Dict[str, Any], readings: Dict[str, float], meta: Dict[str, Any]) -> None:
        if self._machine_id is None or self._sensor_id is None:
            return

        drift_score = float(meta.get("drift_score", 0.0))
        wear_risk_score = 0.0
        if ai_result.get("rul") is not None:
            try:
                wear_risk_score = float(1.0 - (float(ai_result.get("rul")) / 100.0))
                wear_risk_score = max(0.0, min(1.0, wear_risk_score))
            except Exception:
                wear_risk_score = 0.0

        async with AsyncSessionLocal() as session:
            pred = PredictionCreate(
                machine_id=self._machine_id,
                sensor_id=self._sensor_id,
                timestamp=ts,
                prediction=ai_result.get("prediction", "normal"),
                status=ai_result.get("status", "normal"),
                score=float(ai_result.get("score", 0.0)),
                confidence=float(ai_result.get("confidence", 0.0)),
                anomaly_type=ai_result.get("anomaly_type"),
                model_version=ai_result.get("model_version", "unknown"),
                remaining_useful_life=ai_result.get("rul"),
                response_time_ms=float(ai_result.get("response_time_ms", 0.0)),
                contributing_features=ai_result.get("contributing_features"),
                metadata={
                    "source": "mssql",
                    "trend_date": ts.isoformat(),
                    "snapshot": readings,
                    "anomaly_score": float(ai_result.get("score", 0.0)),
                    "drift_score": drift_score,
                    "wear_risk_score": wear_risk_score,
                    "feature_window": meta,
                    "ai_raw": ai_result,
                },
            )
            await prediction_service.create_prediction(session, pred)

    async def _score_with_ai_service(self, *, ts: datetime, readings: Dict[str, float]) -> Dict[str, Any]:
        if self._machine_id is None or self._sensor_id is None:
            return {}

        payload = PredictionRequest(
            sensor_id=self._sensor_id,
            machine_id=self._machine_id,
            timestamp=ts,
            value=float(readings.get("pressure", 0.0)),
            context={"readings": readings},
        )
        result = await prediction_service.call_ai_service(payload)
        return result

    async def _run(self) -> None:
        await self._ensure_machine_and_sensor()

        while not self._stop.is_set():
            try:
                await self._load_runtime_config()

                if not self._effective_enabled:
                    await asyncio.sleep(2)
                    continue

                if not self.host or not self.username or not self.password:
                    logger.error(
                        "MSSQL extruder poller enabled but missing connection settings (host/user/password)."
                    )
                    await asyncio.sleep(5)
                    continue

                now = datetime.utcnow()
                if self._next_retry_at and now < self._next_retry_at:
                    await asyncio.sleep(1)
                    continue

                new_rows = await asyncio.to_thread(self._fetch_rows_sync)
                if new_rows:
                    for r in new_rows:
                        self._window.append(r)
                    self._window.sort(key=lambda x: x.trend_date)
                    self._trim_window()

                    self._last_trend_date = self._window[-1].trend_date

                    readings, meta = self._compute_features()
                    ts = self._window[-1].trend_date

                    ai_result = await self._score_with_ai_service(ts=ts, readings=readings)
                    await self._persist_prediction(ts=ts, ai_result=ai_result, readings=readings, meta=meta)

                    logger.info(
                        "MSSQL extruder tick: ts={}, score={}, status={}, drift={}, window_points={}",
                        ts.isoformat(),
                        ai_result.get("score"),
                        ai_result.get("status"),
                        meta.get("drift_score"),
                        meta.get("window_size"),
                    )

                self._consecutive_failures = 0
                self._next_retry_at = None
            except Exception as e:
                self._consecutive_failures += 1
                backoff = min(self._max_backoff_seconds, 2 ** min(self._consecutive_failures, 8))
                self._next_retry_at = datetime.utcnow() + timedelta(seconds=backoff)
                logger.error(
                    "MSSQL extruder poller error (attempt={} backoff_s={}): {}",
                    self._consecutive_failures,
                    backoff,
                    str(e),
                )

            await asyncio.sleep(self.poll_interval_seconds)


def build_mssql_extruder_poller_from_env() -> MSSQLExtruderPoller:
    import os

    # Master enable: if false, poller will not start at all.
    # Runtime enable/disable is controlled via DB (UI) setting connections.mssql.enabled.
    enabled = os.getenv("MSSQL_ENABLED", "true").lower() in {"1", "true", "yes"}

    host = os.getenv("MSSQL_HOST", "")
    port = int(os.getenv("MSSQL_PORT", "1433"))
    username = os.getenv("MSSQL_USER", "")
    password = os.getenv("MSSQL_PASSWORD", "")
    database = os.getenv("MSSQL_DATABASE", "HISTORISCH")
    table = os.getenv("MSSQL_TABLE", "Tab_Actual")

    poll_interval_seconds = int(os.getenv("MSSQL_POLL_INTERVAL_SECONDS", "60"))
    window_minutes = int(os.getenv("MSSQL_WINDOW_MINUTES", "10"))
    max_rows_per_poll = int(os.getenv("MSSQL_MAX_ROWS_PER_POLL", "5000"))

    machine_name = os.getenv("MSSQL_MACHINE_NAME", "Extruder-SQL")
    sensor_name = os.getenv("MSSQL_SENSOR_NAME", "Extruder SQL Snapshot")

    return MSSQLExtruderPoller(
        enabled=enabled,
        host=host,
        port=port,
        username=username,
        password=password,
        database=database,
        table=table,
        poll_interval_seconds=poll_interval_seconds,
        window_minutes=window_minutes,
        max_rows_per_poll=max_rows_per_poll,
        machine_name=machine_name,
        sensor_name=sensor_name,
    )


mssql_extruder_poller = build_mssql_extruder_poller_from_env()
