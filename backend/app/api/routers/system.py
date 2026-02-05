from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.core.config import get_settings
from app.models.alarm import Alarm
from app.models.ticket import Ticket
from app.services import user_service
from app.services.incident_manager import incident_manager

router = APIRouter(prefix="/system", tags=["system"])
settings = get_settings()
oauth2_optional = OAuth2PasswordBearer(tokenUrl="/users/login", auto_error=False)

@router.post("/reset")
async def reset_system_state(
    session: AsyncSession = Depends(get_session),
    token: str | None = Depends(oauth2_optional),
):
    """MANDATORY: Clean-slate reset.

    Deletes:
    - All alarms
    - All tickets

    Clears:
    - Runtime incident state (prevents immediate re-trigger due to cached state)
    """

    allow_public = os.getenv("ALLOW_PUBLIC_SYSTEM_RESET", "false").lower() in {"1", "true", "yes"}
    if not allow_public:
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            email: str | None = payload.get("sub")
            if not email:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

        user = await user_service.get_user_by_email(session, email)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        if (user.role or "").lower() != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")

    # Tickets first (FK to alarm)
    tickets_deleted = await session.execute(delete(Ticket))
    alarms_deleted = await session.execute(delete(Alarm))
    await session.commit()

    incident_manager.reset_runtime_state()

    return {
        "ok": True,
        "tickets_deleted": tickets_deleted.rowcount or 0,
        "alarms_deleted": alarms_deleted.rowcount or 0,
    }
