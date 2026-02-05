from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import Settings
from app.schemas.settings import SettingsCreate, SettingsUpdate


async def get_setting(session: AsyncSession, key: str) -> Optional[Settings]:
    """Get a setting by key"""
    result = await session.execute(select(Settings).where(Settings.key == key))
    return result.scalar_one_or_none()


async def get_settings(
    session: AsyncSession,
    category: Optional[str] = None,
    is_public: Optional[bool] = None,
) -> List[Settings]:
    """Get all settings, optionally filtered by category or public flag"""
    query = select(Settings)
    if category:
        query = query.where(Settings.category == category)
    if is_public is not None:
        query = query.where(Settings.is_public == is_public)
    result = await session.execute(query)
    return list(result.scalars().all())


async def create_setting(session: AsyncSession, setting_data: SettingsCreate) -> Settings:
    """Create a new setting"""
    setting = Settings(**setting_data.model_dump())
    session.add(setting)
    await session.commit()
    await session.refresh(setting)
    return setting


async def update_setting(
    session: AsyncSession,
    setting: Settings,
    setting_data: SettingsUpdate,
) -> Settings:
    """Update an existing setting"""
    update_data = setting_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(setting, key, value)
    await session.commit()
    await session.refresh(setting)
    return setting


async def delete_setting(session: AsyncSession, setting: Settings) -> None:
    """Delete a setting"""
    await session.delete(setting)
    await session.commit()

