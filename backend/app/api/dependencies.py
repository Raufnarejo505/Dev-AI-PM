from typing import List
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_session
from app.models.user import User
from app.services import user_service

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/users/login")
settings = get_settings()


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(reusable_oauth2),
) -> User:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    user = await user_service.get_user_by_email(session, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def require_roles(allowed_roles: List[str]):
    """Dependency factory for role-based access control"""
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        # Normalize roles to be case-insensitive so legacy users with
        # roles like "ADMIN" still pass checks that expect "admin".
        user_role = (current_user.role or "").lower()
        normalized_allowed = [r.lower() for r in allowed_roles]
        if user_role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}",
            )
        return current_user
    return role_checker


# Common role dependencies
require_admin = require_roles(["admin"])
require_engineer = require_roles(["admin", "engineer"])
require_viewer = require_roles(["admin", "engineer", "viewer"])

# New users get full admin access - default_user_with_full_access role
# This allows new registrations to see full dashboard like admin
def require_full_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Allow all authenticated users (including new registrations) full admin access.
    New users are assigned 'admin' role by default in user_service.create_user()
    This ensures new registrations see full dashboard like admin.
    """
    # All authenticated users get full access - no role restriction
    return current_user


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    if request.client:
        return request.client.host
    return "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request"""
    return request.headers.get("user-agent", "unknown")


__all__ = ["get_session", "get_current_user", "require_roles", "require_admin", "require_engineer", "require_viewer", "require_full_access", "get_client_ip", "get_user_agent"]

