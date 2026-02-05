from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class OPCUANodeConfig:
    node_id: str
    alias: str
    unit: str | None = None
    category: str | None = None


@dataclass
class OPCUASourceConfig:
    """
    In-memory representation of an OPC UA data source.

    NOTE: For now this registry is in-memory only. The structure mirrors the
    kinds of fields we use for MQTT sources so that it can later be persisted
    to the database without changing callers.
    """

    id: str
    name: str
    endpoint_url: str
    namespace_index: int
    sampling_interval_ms: int
    session_timeout_ms: int
    security_mode: str  # "anonymous" | "username_password" | "certificate"
    security_policy: str
    security_mode_level: str
    username: Optional[str] = None
    password: Optional[str] = None
    ca_cert_pem: Optional[str] = None
    client_cert_pem: Optional[str] = None
    client_key_pem: Optional[str] = None

    timestamp_source: str = "server"
    deduplication_enabled: bool = True
    unit_override_policy: str = "preserve"

    db_type: str = "timescale"  # or "influx"
    db_name: str = "pm_db"
    tags: Dict[str, str] = field(default_factory=dict)
    retention_policy: Optional[str] = None
    store_and_forward_enabled: bool = True

    nodes: List[OPCUANodeConfig] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    active: bool = False


class OPCUASourceRegistry:
    """Simple in-memory registry for active OPC UA sources."""

    def __init__(self) -> None:
        self._sources: Dict[str, OPCUASourceConfig] = {}

    def upsert(self, source: OPCUASourceConfig) -> None:
        source.updated_at = datetime.utcnow()
        self._sources[source.id] = source

    def get(self, source_id: str) -> Optional[OPCUASourceConfig]:
        return self._sources.get(source_id)

    def all(self) -> List[OPCUASourceConfig]:
        return list(self._sources.values())

    def mark_active(self, source_id: str, active: bool) -> None:
        cfg = self._sources.get(source_id)
        if not cfg:
            return
        cfg.active = active
        cfg.updated_at = datetime.utcnow()


registry = OPCUASourceRegistry()



