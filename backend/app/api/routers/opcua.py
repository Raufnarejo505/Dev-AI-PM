from __future__ import annotations

import asyncio
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_session
from app.core.config import get_settings
from app.models.user import User
from app.opcua.connector import opcua_connector
from app.opcua.source_registry import OPCUANodeConfig, OPCUASourceConfig, registry


router = APIRouter(prefix="/opcua", tags=["opcua"])

settings = get_settings()


class OPCUANodeIn(BaseModel):
    node_id: str
    alias: str
    unit: str | None = None
    category: str | None = None


class OPCUAConfigIn(BaseModel):
    name: str = "OPC UA Source"
    endpoint_url: str
    namespace_index: int = 2
    sampling_interval_ms: int = 1_000
    session_timeout_ms: int = 60_000

    security_mode: str = "anonymous"
    security_policy: str | None = None
    security_mode_level: str | None = None
    username: str | None = None
    password: str | None = None
    ca_cert_pem: str | None = None
    client_cert_pem: str | None = None
    client_key_pem: str | None = None

    timestamp_source: str = "server"
    deduplication_enabled: bool = True
    unit_override_policy: str = "preserve"

    db_type: str = "timescale"
    db_name: str = settings.postgres_db
    tags: Dict[str, str] = {}
    retention_policy: str | None = None
    store_and_forward_enabled: bool = True

    nodes: List[OPCUANodeIn]


@router.get("/status")
async def get_opcua_status(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Return high‑level heartbeat and node count for OPC UA connector."""
    heartbeat = opcua_connector.heartbeat_timestamp
    return {
        "connected": heartbeat is not None,
        "heartbeat_ts": heartbeat,
        "node_count": opcua_connector.node_count,
        "last_error": opcua_connector.last_error,
        "sources": [
            {
                "id": s.id,
                "name": s.name,
                "endpoint_url": s.endpoint_url,
                "active": s.active,
                "node_count": len(s.nodes),
            }
            for s in registry.all()
        ],
    }


@router.post("/test")
async def test_connection(
    payload: OPCUAConfigIn,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Perform a real connection test to the OPC UA server.
    Attempts to connect and read values from the configured nodes.
    """
    from datetime import datetime
    
    handshake_logs: List[str] = []
    sample_preview: List[Dict[str, Any]] = []
    
    handshake_logs.append(f"Preparing OPC UA connection test to {payload.endpoint_url}")
    
    try:
        # Validate payload first
        if not payload.endpoint_url:
            raise HTTPException(status_code=400, detail="Endpoint URL is required")
        if not payload.nodes:
            raise HTTPException(status_code=400, detail="At least one node must be configured")
        
        handshake_logs.append("Configuration payload validated")
        
        # Try to import asyncua
        try:
            from asyncua import Client, ua
        except ImportError:
            handshake_logs.append("asyncua library not installed - connection test skipped")
            handshake_logs.append("Install with: pip install asyncua")
            return {
                "ok": False,
                "handshake_logs": handshake_logs,
                "sample_preview": [],
                "error": "asyncua library not installed"
            }
        
        # Attempt actual connection
        handshake_logs.append(f"Attempting to connect to {payload.endpoint_url}...")
        
        try:
            async with Client(url=payload.endpoint_url) as client:
                handshake_logs.append("Successfully connected to OPC UA server")
                
                # Configure security if needed
                if payload.security_mode.lower() != "anonymous":
                    if payload.username and payload.password:
                        client.set_user(payload.username)
                        client.set_password(payload.password)
                        handshake_logs.append(f"Authenticated as {payload.username}")
                
                # Try to read from first few nodes
                nodes_to_test = payload.nodes[:3] if len(payload.nodes) > 3 else payload.nodes
                
                for node_cfg in nodes_to_test:
                    try:
                        handshake_logs.append(f"Reading node: {node_cfg.node_id}")
                        node = client.get_node(node_cfg.node_id)
                        value = await node.read_value()
                        data_value = await node.read_data_value()
                        quality = str(getattr(data_value, "StatusCode", "Good"))
                        ts = getattr(data_value, "SourceTimestamp", None)
                        
                        sample_preview.append({
                            "timestamp": ts.isoformat() if ts else datetime.utcnow().isoformat() + "Z",
                            "alias": node_cfg.alias,
                            "value": float(value) if isinstance(value, (int, float)) else 0.0,
                            "quality": quality,
                            "unit": node_cfg.unit or "",
                            "node_id": node_cfg.node_id,
                        })
                        handshake_logs.append(f"Node {node_cfg.node_id} read successfully: {value}")
                    except Exception as node_exc:
                        handshake_logs.append(f"Failed to read node {node_cfg.node_id}: {str(node_exc)}")
                        sample_preview.append({
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "alias": node_cfg.alias,
                            "value": 0.0,
                            "quality": "Bad",
                            "unit": node_cfg.unit or "",
                            "node_id": node_cfg.node_id,
                            "error": str(node_exc),
                        })
                
                handshake_logs.append(f"Connection test completed - {len(sample_preview)} node(s) tested")
                
                return {
                    "ok": True,
                    "handshake_logs": handshake_logs,
                    "sample_preview": sample_preview,
                }
                
        except Exception as conn_exc:
            error_msg = str(conn_exc)
            handshake_logs.append(f"Connection failed: {error_msg}")
            
            # Provide helpful error messages
            if "Connection refused" in error_msg or "timeout" in error_msg.lower():
                handshake_logs.append("Check if OPC UA server is running and accessible")
                handshake_logs.append("Verify endpoint URL and port are correct")
                handshake_logs.append("Check firewall settings")
            elif "Name resolution" in error_msg or "getaddrinfo" in error_msg:
                handshake_logs.append("Check hostname/IP address is correct")
                handshake_logs.append("Try using IP address instead of hostname")
            
            return {
                "ok": False,
                "handshake_logs": handshake_logs,
                "sample_preview": [],
                "error": error_msg,
            }
            
    except HTTPException:
        raise
    except Exception as exc:
        error_msg = str(exc)
        handshake_logs.append(f"Test failed: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)


@router.post("/activate")
async def activate_source(
    payload: OPCUAConfigIn,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Register / update an OPC UA source and mark it active."""
    source_id = str(uuid4())
    nodes = [
        OPCUANodeConfig(
            node_id=n.node_id,
            alias=n.alias,
            unit=n.unit,
            category=n.category,
        )
        for n in payload.nodes
    ]

    cfg = OPCUASourceConfig(
        id=source_id,
        name=payload.name,
        endpoint_url=payload.endpoint_url,
        namespace_index=payload.namespace_index,
        sampling_interval_ms=payload.sampling_interval_ms,
        session_timeout_ms=payload.session_timeout_ms,
        security_mode=payload.security_mode,
        security_policy=payload.security_policy or "",
        security_mode_level=payload.security_mode_level or "",
        username=payload.username,
        password=payload.password,
        ca_cert_pem=payload.ca_cert_pem,
        client_cert_pem=payload.client_cert_pem,
        client_key_pem=payload.client_key_pem,
        timestamp_source=payload.timestamp_source,
        deduplication_enabled=payload.deduplication_enabled,
        unit_override_policy=payload.unit_override_policy,
        db_type=payload.db_type,
        db_name=payload.db_name,
        tags=payload.tags or {},
        retention_policy=payload.retention_policy,
        store_and_forward_enabled=payload.store_and_forward_enabled,
        nodes=nodes,
        active=True,
    )

    registry.upsert(cfg)
    registry.mark_active(cfg.id, True)

    # Ensure background worker is running
    loop = opcua_connector._loop  # type: ignore[attr-defined]
    if loop is None:
        loop = asyncio.get_event_loop()
        opcua_connector.start(loop)

    return {"id": cfg.id, "name": cfg.name, "node_count": len(cfg.nodes)}



