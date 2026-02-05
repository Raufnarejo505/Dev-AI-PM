from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_current_user, require_admin, require_engineer
from app.models.user import User
from app.schemas.settings import SettingsCreate, SettingsRead, SettingsUpdate
from app.services import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=List[SettingsRead])
async def get_settings(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_engineer),
    category: str = None,
):
    """Get system settings"""
    if category:
        settings_list = await settings_service.get_settings(session, category=category)
    else:
        settings_list = await settings_service.get_settings(session)
    return settings_list


@router.get("/{key}", response_model=SettingsRead)
async def get_setting(
    key: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_engineer),
):
    """Get a specific setting by key"""
    setting = await settings_service.get_setting(session, key)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting


@router.patch("/{key}", response_model=SettingsRead)
async def update_setting(
    key: str,
    payload: SettingsUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Update a setting (admin only)"""
    setting = await settings_service.get_setting(session, key)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return await settings_service.update_setting(session, setting, payload)


@router.post("", response_model=SettingsRead, status_code=status.HTTP_201_CREATED)
async def create_setting(
    payload: SettingsCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Create a new setting (admin only)"""
    existing = await settings_service.get_setting(session, payload.key)
    if existing:
        raise HTTPException(status_code=400, detail="Setting with this key already exists")
    return await settings_service.create_setting(session, payload)

