from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


async def create_user(session: AsyncSession, payload: UserCreate) -> User:
    # New users get full admin access by default (default_user_with_full_access)
    # This ensures new registrations see full dashboard like admin
    default_role = payload.role or "admin"  # Default to admin for full access
    
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        role=default_role,
        hashed_password=get_password_hash(payload.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def authenticate(session: AsyncSession, email: str, password: str) -> Optional[User]:
    # Optimized: Single query with email index
    result = await session.execute(select(User).where(User.email == email).limit(1))
    user = result.scalars().first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None


async def update_user(session: AsyncSession, user: User, payload: UserUpdate) -> User:
    """Update user profile"""
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.password is not None:
        user.hashed_password = get_password_hash(payload.password)
    await session.commit()
    await session.refresh(user)
    return user

