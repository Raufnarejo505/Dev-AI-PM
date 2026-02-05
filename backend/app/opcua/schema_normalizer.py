from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def normalize_opcua_sample(
    *,
    alias: str,
    value: Any,
    quality: str = "Good",
    unit: Optional[str] = None,
    timestamp_source: str = "server",
    server_timestamp: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Normalize a single OPC UA value change into the fixed JSON payload format.

    Payload shape (fixed):
        {
            "timestamp": "...",
            "alias": "motor_current",
            "value": 12.3,
            "quality": "Good",
            "unit": "A",
        }
    """

    if server_timestamp is None:
        ts = datetime.now(timezone.utc)
    else:
        ts = server_timestamp.astimezone(timezone.utc)

    return {
        "timestamp": ts.isoformat(),
        "alias": alias,
        "value": value,
        "quality": quality or "Good",
        "unit": unit or "",
    }



