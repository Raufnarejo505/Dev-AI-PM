import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, require_admin, require_engineer
from app.models.user import User
from app.schemas.connections import ConnectionsRead, ConnectionsUpdate, MSSQLTestRequest, MSSQLTestResponse, MSSQLConfig
from app.schemas.settings import SettingsCreate, SettingsUpdate
from app.services import settings_service


router = APIRouter(prefix="/connections", tags=["connections"])

EDGE_PC_KEY = "connections.edge_pc"
MSSQL_KEY = "connections.mssql"


def _loads_json(value: Optional[str]) -> Optional[Dict[str, Any]]:
    if not value:
        return None
    try:
        return json.loads(value)
    except Exception:
        return None


def _mask_password(cfg: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(cfg)
    if out.get("password"):
        out["password"] = "********"
    return out


async def _upsert_setting(
    session: AsyncSession,
    *,
    key: str,
    value: str,
    value_type: str,
    category: str,
    description: str,
    is_public: bool,
) -> None:
    existing = await settings_service.get_setting(session, key)
    if existing:
        await settings_service.update_setting(
            session,
            existing,
            SettingsUpdate(
                value=value,
                value_type=value_type,
                category=category,
                description=description,
                is_public=is_public,
            ),
        )
    else:
        await settings_service.create_setting(
            session,
            SettingsCreate(
                key=key,
                value=value,
                value_type=value_type,
                category=category,
                description=description,
                is_public=is_public,
            ),
        )


@router.get("", response_model=ConnectionsRead)
async def get_connections(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_engineer),
):
    edge_pc_setting = await settings_service.get_setting(session, EDGE_PC_KEY)
    mssql_setting = await settings_service.get_setting(session, MSSQL_KEY)

    edge_pc_raw = _loads_json(edge_pc_setting.value if edge_pc_setting else None)
    mssql_raw = _loads_json(mssql_setting.value if mssql_setting else None) or {}

    if mssql_raw:
        mssql_raw = _mask_password(mssql_raw)

    mssql_cfg = MSSQLConfig(**mssql_raw) if mssql_raw else MSSQLConfig()

    return ConnectionsRead(edge_pc=edge_pc_raw, mssql=mssql_cfg)


@router.put("", response_model=ConnectionsRead)
async def update_connections(
    payload: ConnectionsUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    if payload.edge_pc is not None:
        await _upsert_setting(
            session,
            key=EDGE_PC_KEY,
            value=json.dumps(payload.edge_pc.model_dump()),
            value_type="json",
            category="connections",
            description="Edge PC connection settings",
            is_public=False,
        )

    if payload.mssql is not None:
        existing = await settings_service.get_setting(session, MSSQL_KEY)
        existing_cfg = _loads_json(existing.value if existing else None) or {}

        incoming = payload.mssql.model_dump(exclude_unset=True)
        if incoming.get("password") in (None, "", "********"):
            incoming.pop("password", None)

        merged = {**existing_cfg, **incoming}

        await _upsert_setting(
            session,
            key=MSSQL_KEY,
            value=json.dumps(merged),
            value_type="json",
            category="connections",
            description="MSSQL extruder connection settings",
            is_public=False,
        )

    return await get_connections(session=session, current_user=current_user)


@router.post("/test/mssql", response_model=MSSQLTestResponse)
async def test_mssql_connection(
    payload: MSSQLTestRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_engineer),
):
    mssql_setting = await settings_service.get_setting(session, MSSQL_KEY)
    stored_raw = _loads_json(mssql_setting.value if mssql_setting else None) or {}

    if payload.config is None:
        merged = dict(stored_raw)
    else:
        incoming = payload.config.model_dump(exclude_unset=True)
        incoming_pwd = (incoming.get("password") or "").strip() if isinstance(incoming.get("password"), str) else incoming.get("password")
        if incoming_pwd in (None, "", "********"):
            incoming.pop("password", None)
        merged = {**stored_raw, **incoming}

    cfg = MSSQLConfig(**merged) if merged else MSSQLConfig()

    if not cfg.host or not cfg.username or not cfg.password:
        raise HTTPException(status_code=400, detail="Missing MSSQL host/user/password")

    def _test_sync() -> None:
        import pymssql

        conn = pymssql.connect(
            server=cfg.host,
            user=cfg.username,
            password=cfg.password,
            database=cfg.database,
            port=cfg.port,
            login_timeout=5,
            timeout=5,
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
            cur.execute("SELECT 1 AS ok")
            cur.fetchone()
        finally:
            conn.close()

    try:
        import asyncio

        await asyncio.to_thread(_test_sync)
        return MSSQLTestResponse(ok=True, message="Connection successful")
    except Exception as e:
        return MSSQLTestResponse(ok=False, message=f"Connection failed: {e}")
