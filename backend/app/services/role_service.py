from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate, PermissionUpdate


async def get_role(session: AsyncSession, role_id: UUID) -> Optional[Role]:
    """Get a role by ID"""
    result = await session.execute(select(Role).where(Role.id == role_id))
    return result.scalar_one_or_none()


async def get_role_by_name(session: AsyncSession, name: str) -> Optional[Role]:
    """Get a role by name"""
    result = await session.execute(select(Role).where(Role.name == name))
    return result.scalar_one_or_none()


async def list_roles(session: AsyncSession) -> List[Role]:
    """List all roles"""
    result = await session.execute(select(Role).order_by(Role.name))
    return list(result.scalars().all())


async def create_role(session: AsyncSession, role_data: RoleCreate) -> Role:
    """Create a new role"""
    role = Role(
        name=role_data.name,
        description=role_data.description,
        permissions_json=role_data.permissions,
    )
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role


async def update_role(
    session: AsyncSession,
    role: Role,
    role_data: RoleUpdate,
) -> Role:
    """Update an existing role"""
    update_data = role_data.model_dump(exclude_unset=True)
    if "permissions" in update_data:
        role.permissions_json = update_data.pop("permissions")
    for key, value in update_data.items():
        setattr(role, key, value)
    await session.commit()
    await session.refresh(role)
    return role


async def update_role_permissions(
    session: AsyncSession,
    role: Role,
    permissions_data: PermissionUpdate,
) -> Role:
    """Update role permissions"""
    role.permissions_json = permissions_data.permissions
    await session.commit()
    await session.refresh(role)
    return role


async def delete_role(session: AsyncSession, role: Role) -> None:
    """Delete a role (cannot delete system roles)"""
    if role.is_system == "true":
        raise ValueError("Cannot delete system role")
    await session.delete(role)
    await session.commit()

