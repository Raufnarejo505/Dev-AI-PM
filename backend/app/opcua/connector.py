from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.config import Settings, get_settings
from app.db.session import AsyncSessionLocal
from app.opcua.schema_normalizer import normalize_opcua_sample
from app.opcua.source_registry import OPCUASourceConfig, registry
from app.services import sensor_data_service, sensor_service, machine_service
from app.services.extruder_ai_service import extruder_ai_service

try:
    # asyncua is a popular async OPC UA client library
    from asyncua import Client, ua
except Exception:  # pragma: no cover - optional dependency
    Client = None  # type: ignore
    ua = None  # type: ignore


class OPCUAConnector:
    """
    Long‑running worker that establishes OPC UA sessions and subscribes to
    configured nodes. It mirrors the behaviour of the MQTTIngestor but for
    OPC UA subscriptions.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._heartbeat_ts: Optional[float] = None
        self._last_error: Optional[str] = None
        self._active_nodes_count: int = 0

    # Public status ---------------------------------------------------------
    @property
    def heartbeat_timestamp(self) -> Optional[float]:
        return self._heartbeat_ts

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    @property
    def node_count(self) -> int:
        return self._active_nodes_count

    # Lifecycle -------------------------------------------------------------
    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        if self._running:
            return
        self._loop = loop
        self._running = True
        self._task = loop.create_task(self._run(), name="opcua-connector")
        logger.info("OPC UA connector worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("OPC UA connector worker stopped")

    # Core worker loop ------------------------------------------------------
    async def _run(self) -> None:
        """
        Iterate over all active sources in the registry and ensure there is an
        active subscription for each. If asyncua is not installed we still keep
        the worker alive and simply log a warning – this avoids breaking the
        rest of the stack.
        """
        if Client is None:
            logger.warning(
                "asyncua library is not installed – OPC UA connector will run in "
                "no‑op mode. Install 'asyncua' to enable real OPC UA ingestion."
            )

        while self._running:
            try:
                active_sources = [s for s in registry.all() if s.active]
                self._active_nodes_count = sum(len(s.nodes) for s in active_sources)
                self._heartbeat_ts = asyncio.get_event_loop().time()

                # For now we keep a simple sequential loop; each iteration
                # re‑creates short‑lived sessions to pull a sample from every
                # configured node. This keeps the implementation lightweight
                # while still honouring sampling_interval_ms.
                for source in active_sources:
                    await self._poll_source_once(source)

                # Sleep for the minimum configured sampling interval
                if active_sources:
                    min_interval_ms = min(s.sampling_interval_ms for s in active_sources)
                else:
                    min_interval_ms = 5_000
                await asyncio.sleep(max(min_interval_ms / 1000.0, 1.0))
            except asyncio.CancelledError:
                break
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("OPC UA connector loop error: {}", exc, exc_info=True)
                self._last_error = str(exc)
                await asyncio.sleep(5)

    async def _poll_source_once(self, source: OPCUASourceConfig) -> None:
        """Fetch one sample for every configured node of a source."""
        if Client is None:
            # No real OPC UA library available – emit fake heartbeat only.
            logger.warning("OPC UA client unavailable; skipping real polling for {}. Install asyncua: pip install asyncua", source.id)
            self._last_error = "asyncua library not installed"
            return

        try:
            logger.debug("Connecting to OPC UA server: {}", source.endpoint_url)
            async with Client(url=source.endpoint_url, timeout=10) as client:
                # Basic security handling – full Sign&Encrypt is delegated to
                # asyncua; we only configure based on the mode/policy flags.
                if ua is not None:
                    if source.security_mode.lower() != "anonymous":
                        if source.username and source.password:
                            client.set_user(source.username)
                            client.set_password(source.password)
                            logger.debug("Using username/password authentication for {}", source.id)

                # Simple node sampling
                nodes_read = 0
                for node_cfg in source.nodes:
                    try:
                        node = client.get_node(node_cfg.node_id)
                        value = await node.read_value()
                        data_value = await node.read_data_value()
                        quality = str(getattr(data_value, "StatusCode", "Good"))
                        ts = getattr(data_value, "SourceTimestamp", None)

                        sample = normalize_opcua_sample(
                            alias=node_cfg.alias,
                            value=value,
                            quality=quality,
                            unit=node_cfg.unit,
                            timestamp_source=source.timestamp_source,
                            server_timestamp=ts,
                        )
                        await self._route_sample(source, node_cfg, sample)
                        nodes_read += 1
                    except Exception as node_exc:
                        logger.warning("Failed to read node {} from source {}: {}", 
                                     node_cfg.node_id, source.id, node_exc)
                        # Continue with other nodes even if one fails
                        continue
                
                if nodes_read > 0:
                    logger.debug("Successfully read {} node(s) from OPC UA source {}", nodes_read, source.id)
                    self._last_error = None  # Clear error on success

        except asyncio.TimeoutError:
            error_msg = f"Connection timeout to {source.endpoint_url}"
            logger.error("OPC UA connection timeout for source {}: {}", source.id, error_msg)
            self._last_error = error_msg
        except ConnectionError as conn_err:
            error_msg = f"Connection error: {str(conn_err)}"
            logger.error("OPC UA connection error for source {}: {}", source.id, error_msg)
            self._last_error = error_msg
        except Exception as exc:
            error_msg = f"Error polling OPC UA source {source.id}: {str(exc)}"
            logger.error(error_msg)
            self._last_error = str(exc)

    async def _route_sample(
        self,
        source: OPCUASourceConfig,
        node_cfg: Any,
        sample: Dict[str, Any],
    ) -> None:
        """
        Route a normalized OPC UA sample into the existing sensor/machine +
        sensor_data pipeline. This mirrors the logic used in the MQTT ingestor
        but starts from the fixed OPC UA payload shape.
        """
        alias = sample["alias"]
        value = sample["value"]

        async with AsyncSessionLocal() as session:
            # 1. Ensure machine exists (use tags to build a synthetic machine id)
            # Default to extruder-01 to match the project requirement that OPC UA should
            # drive a single extruder machine and the AI decision layer should run.
            machine_key = source.tags.get("machine") or "extruder-01"
            machine = await machine_service.get_machine(session, machine_key)
            if not machine:
                from app.schemas.machine import MachineCreate

                machine = await machine_service.create_machine(
                    session,
                    MachineCreate(
                        name=machine_key,
                        status="online",
                        location=source.tags.get("line", ""),
                        metadata={
                            "source": "opcua",
                            "source_id": source.id,
                            "type": source.tags.get("type") or source.tags.get("machine_type") or "extruder",
                        },
                    ),
                )
                await session.commit()
            else:
                # Ensure machine is tagged as an extruder so the extruder AI decision layer
                # can create alarms/tickets. Do not overwrite if already set.
                md = machine.metadata_json or {}
                if not isinstance(md, dict):
                    md = {}
                if not (md.get("type") or md.get("machine_type")):
                    md["type"] = source.tags.get("type") or source.tags.get("machine_type") or "extruder"
                    machine.metadata_json = md
                    await session.commit()

            # 2. Ensure sensor exists
            sensor = await sensor_service.get_sensor(session, alias)
            if not sensor:
                from app.schemas.sensor import SensorCreate

                # Use category as sensor_type, or default to "opcua" if not provided
                sensor_type = node_cfg.category or "opcua"

                sensor = await sensor_service.create_sensor(
                    session,
                    SensorCreate(
                        name=alias,
                        machine_id=machine.id,
                        sensor_type=sensor_type,
                        unit=node_cfg.unit or "",
                        metadata={
                            "source": "opcua",
                            "opcua_node_id": node_cfg.node_id,
                            "category": node_cfg.category,
                        },
                    ),
                )
                await session.commit()

            # 3. Write sensor data using existing service
            from app.schemas.sensor_data import SensorDataIn

            # Parse timestamp string to datetime object
            timestamp_str = sample["timestamp"]
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            elif isinstance(timestamp_str, datetime):
                timestamp = timestamp_str
            else:
                timestamp = datetime.utcnow()

            data_in = SensorDataIn(
                sensor_id=sensor.id,
                machine_id=machine.id,
                timestamp=timestamp,
                value=float(value) if isinstance(value, (int, float)) else 0.0,
                status=sample.get("quality") or "Good",
                metadata={
                    "unit": sample.get("unit"),
                    "source": "opcua",
                    "alias": alias,
                },
            )
            sensor_data_record = await sensor_data_service.ingest_sensor_data(session, data_in)
            await session.commit()

            # If this sample is a profile signal, store it but do not generate alarms/tickets.
            # Industrial calmness rule: no alarms/tickets from ingestion metadata.
            alias_lower = (alias or "").lower()
            is_profile_signal = "simulationprofile" in alias_lower or alias_lower in {"profile", "simulation_profile"}
            if is_profile_signal:
                return

            # Broadcast real-time update
            try:
                from app.api.routers.realtime import broadcast_update
                await broadcast_update(
                    "sensor_data.created",
                    {
                        "id": str(sensor_data_record.id),
                        "machine_id": str(machine.id),
                        "sensor_id": str(sensor.id),
                        "value": float(sensor_data_record.value),
                        "timestamp": sensor_data_record.timestamp.isoformat(),
                    },
                )
            except Exception as e:
                logger.debug(f"Failed to broadcast sensor data update: {e}")

            # 4. Call AI Service for Prediction
            try:
                import httpx
                import time
                from app.services.feature_service import FeatureService
                
                ai_service_url = self.settings.ai_service_url
                
                # Prepare readings - use sensor alias/name for AI threshold matching
                # AI service uses sensor names like "pressure", "temperature", "vibration", "motor_current"
                sensor_name = alias.lower() if alias else sensor.name.lower() if sensor.name else "value"
                
                # Map OPC UA sensor names to AI service expected names
                sensor_name_mapping = {
                    "pressure": "pressure",
                    "temp": "temperature",
                    "temperature": "temperature",
                    "vibration": "vibration",
                    "vib": "vibration",
                    "current": "motor_current",
                    "motor_current": "motor_current",
                    "motorcurrent": "motor_current",
                    "wear": "wear_index",
                    "wear_index": "wear_index",
                    "wearindex": "wear_index",
                }
                
                # Find matching AI sensor name
                ai_sensor_name = "value"  # Default
                for key, mapped_name in sensor_name_mapping.items():
                    if key in sensor_name:
                        ai_sensor_name = mapped_name
                        break
                
                # Prepare readings with mapped sensor name
                raw_readings = {ai_sensor_name: float(value)}
                
                # Validate and prepare readings using feature service
                validated_readings = FeatureService.prepare_for_ai(raw_readings)
                
                if not validated_readings:
                    logger.warning("No valid readings after validation, skipping AI prediction")
                else:
                    predict_payload = {
                        "machine_id": str(machine.id),
                        "sensor_id": str(sensor.id),
                        "timestamp": timestamp.isoformat(),
                        "readings": validated_readings,
                    }
                    
                    logger.debug(f"Calling AI service: {ai_service_url}/predict for machine={machine.id}, sensor={sensor.id}")
                    start_time = time.time()
                    try:
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            response = await client.post(f"{ai_service_url}/predict", json=predict_payload)
                            inference_latency_ms = (time.time() - start_time) * 1000
                            
                            if response.status_code == 200:
                                prediction_result = response.json()

                                # 5. Store Prediction
                                from app.services import prediction_service
                                from app.schemas.prediction import PredictionCreate

                                pred_create = PredictionCreate(
                                    machine_id=machine.id,
                                    sensor_id=sensor.id,
                                    timestamp=timestamp,
                                    prediction=prediction_result.get("prediction", "normal"),
                                    status=prediction_result.get("status", "normal"),
                                    score=float(prediction_result.get("score", 0.0)),
                                    confidence=float(prediction_result.get("confidence", 0.0)),
                                    anomaly_type=prediction_result.get("anomaly_type"),
                                    model_version=prediction_result.get("model_version", "unknown"),
                                    remaining_useful_life=prediction_result.get("rul"),
                                    response_time_ms=float(prediction_result.get("response_time_ms", inference_latency_ms)),
                                    contributing_features=prediction_result.get("contributing_features"),
                                    metadata={
                                        **prediction_result,
                                        "inference_latency_ms": inference_latency_ms,
                                        "source": "opcua",
                                    },
                                )
                                prediction = await prediction_service.create_prediction(session, pred_create)
                                await session.commit()
                                logger.info(
                                    "✅ AI Prediction created: machine={}, sensor={}, status={}, score={:.3f}",
                                    machine.name,
                                    alias,
                                    prediction.status,
                                    prediction.score,
                                )

                                # Broadcast WebSocket update for new prediction
                                try:
                                    from app.api.routers.realtime import broadcast_update

                                    await broadcast_update(
                                        "prediction.created",
                                        {
                                            "id": str(prediction.id),
                                            "machine_id": str(machine.id),
                                            "sensor_id": str(sensor.id),
                                            "status": prediction.status,
                                            "confidence": float(prediction.confidence) if prediction.confidence else None,
                                            "timestamp": prediction.timestamp.isoformat(),
                                        },
                                    )
                                except Exception as e:
                                    logger.debug(f"Failed to broadcast prediction update: {e}")

                                # 6. Send email notification for critical/warning predictions
                                prediction_status = prediction_result.get("status", "normal").lower()
                                confidence = float(prediction_result.get("confidence", 0.0))
                                prediction_str = prediction_result.get("prediction", "normal").lower()
                                score = float(prediction_result.get("score", 0.0))

                                if prediction_status in ["warning", "critical"] or prediction_str == "anomaly" or score > 0.7:
                                    try:
                                        from app.services import notification_service

                                        await notification_service.send_prediction_alert_email(
                                            machine_id=str(machine.id),
                                            sensor_id=str(sensor.id),
                                            prediction_status=prediction_status,
                                            score=score,
                                            confidence=confidence,
                                        )
                                    except Exception as e:
                                        logger.warning(f"Failed to send prediction alert email: {e}")

                                # NOTE: Alarm/ticket generation intentionally NOT performed here.
                                # It must be controlled by incident_manager to prevent flooding.
                            else:
                                logger.warning(f"AI service returned status {response.status_code}: {response.text}")
                    except httpx.TimeoutException:
                        logger.error(f"AI service timeout for machine={machine.id}, sensor={alias}")
                    except httpx.RequestError as e:
                        logger.error(f"AI service request error for machine={machine.id}, sensor={alias}: {e}")
                    except Exception as e:
                        logger.error(f"AI service error for machine={machine.id}, sensor={alias}: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Failed to get AI prediction: {e}", exc_info=True)

            # ---------------- Extruder AI decision layer (trend-based) ----------------
            # This MUST be the only source of alarm/ticket creation for industrial calmness.
            # Ingestion only observes signals and stores data; alarms/tickets are created
            # only after the AI layer decides a profile transition.
            try:
                machine_type = ((machine.metadata_json or {}).get("machine_type") or (machine.metadata_json or {}).get("type") or "").lower()
                is_extruder = machine_type == "extruder" or "extruder" in (machine.name or "").lower()

                if is_extruder:
                    canonical_var = None
                    if "temp" in alias_lower or "temperature" in alias_lower:
                        canonical_var = "temperature"
                    elif "motor" in alias_lower and "current" in alias_lower:
                        canonical_var = "motor_current"
                    elif "pressure" in alias_lower:
                        canonical_var = "pressure"
                    elif "vibration" in alias_lower or "vib" in alias_lower:
                        canonical_var = "vibration"
                    elif "wear" in alias_lower:
                        canonical_var = "wear_index"

                    if canonical_var:
                        extruder_ai_service.observe(
                            machine_id=str(machine.id),
                            var_name=canonical_var,
                            value=float(data_in.value or 0.0),
                            timestamp=data_in.timestamp,
                        )
                        decision = extruder_ai_service.decide(machine_id=str(machine.id), now=data_in.timestamp)
                        if decision:
                            await extruder_ai_service.apply_and_maybe_raise_incident(
                                session,
                                machine=machine,
                                observed_at=data_in.timestamp,
                                decision=decision,
                            )
            except Exception as e:
                logger.debug(f"Extruder AI decision layer failed (non-blocking): {e}")


opcua_connector = OPCUAConnector(get_settings())
