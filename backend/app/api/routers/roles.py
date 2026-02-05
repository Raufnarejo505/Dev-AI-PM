from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_current_user, require_admin
from app.models.user import User
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate, PermissionUpdate
from app.services import role_service

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=List[RoleRead])
async def list_roles(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """List all roles (admin only)"""
    return await role_service.list_roles(session)


@router.post("", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Create a new role (admin only)"""
    existing = await role_service.get_role_by_name(session, payload.name)
    if existing:
        raise HTTPException(status_code=400, detail="Role with this name already exists")
    return await role_service.create_role(session, payload)


@router.get("/{role_id}", response_model=RoleRead)
async def get_role(
    role_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Get a role by ID (admin only)"""
    role = await role_service.get_role(session, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.patch("/{role_id}", response_model=RoleRead)
async def update_role(
    role_id: UUID,
    payload: RoleUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Update a role (admin only)"""
    role = await role_service.get_role(session, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return await role_service.update_role(session, role, payload)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Delete a role (admin only, cannot delete system roles)"""
    role = await role_service.get_role(session, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    try:
        await role_service.delete_role(session, role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{role_id}/permissions", response_model=List[str])
async def get_role_permissions(
    role_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Get permissions for a role (admin only)"""
    role = await role_service.get_role(session, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role.permissions_json or []


@router.post("/{role_id}/permissions", response_model=RoleRead)
async def update_role_permissions(
    role_id: UUID,
    payload: PermissionUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Update permissions for a role (admin only)"""
    role = await role_service.get_role(session, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return await role_service.update_role_permissions(session, role, payload)

