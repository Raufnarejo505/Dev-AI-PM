from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, timedelta, timezone
from app.api.dependencies import get_session, get_current_user, get_client_ip, get_user_agent
from app.core.security import (
    create_access_token, create_refresh_token, verify_token, revoke_token,
    revoke_refresh_token, generate_password_reset_token, verify_password, get_password_hash
)
from app.schemas.user import (
    Token, UserCreate, UserRead, UserUpdate, RefreshTokenRequest,
    PasswordResetRequest, PasswordResetConfirm, ChangePasswordRequest
)
from app.services import user_service, audit_service, notification_service
from app.schemas.audit_log import AuditLogCreate
from app.models.user import User
from app.models.password_reset import PasswordResetToken
from loguru import logger

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, session: AsyncSession = Depends(get_session)):
    existing = await user_service.get_user_by_email(session, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    new_user = await user_service.create_user(session, payload)
    
    # Send welcome email notification
    try:
        await notification_service.send_welcome_email(new_user.email, new_user.full_name or new_user.email)
        logger.info(f"Welcome email sent to {new_user.email}")
    except Exception as e:
        logger.warning(f"Failed to send welcome email to {new_user.email}: {e}")
        # Don't fail registration if email fails
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
    request: Request = None,
):
    # Fast authentication - single query
    user = await user_service.authenticate(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create tokens immediately (no DB operations)
    token = create_access_token(subject=user.email)
    refresh_token = create_refresh_token(subject=user.email)
    
    # Return immediately - don't update last_login (removed for speed)
    # Token creation is fast, return immediately
    return Token(access_token=token, refresh_token=refresh_token)


@router.get("/me", response_model=UserRead)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Get current user profile"""
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_current_user_profile(
    payload: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update current user profile"""
    return await user_service.update_user(session, current_user, payload)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    payload: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session),
):
    """Refresh access token using refresh token"""
    payload_data = verify_token(payload.refresh_token, token_type="refresh")
    if not payload_data:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    email = payload_data.get("sub")
    user = await user_service.get_user_by_email(session, email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Create new access token
    new_access_token = create_access_token(subject=user.email)
    # Optionally create new refresh token (rotate)
    new_refresh_token = create_refresh_token(subject=user.email)
    
    return Token(access_token=new_access_token, refresh_token=new_refresh_token)


@router.post("/logout")
async def logout(
    payload: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
):
    """Logout and revoke refresh token"""
    # Revoke refresh token if provided
    if payload.refresh_token:
        token_data = verify_token(payload.refresh_token, token_type="refresh")
        if token_data and token_data.get("jti"):
            revoke_refresh_token(token_data["jti"])
    
    # Note: Access tokens are stateless, so we can't revoke them
    # In production, use a token blacklist (Redis) for access tokens too
    
    return {"message": "Logged out successfully"}


@router.post("/password-reset/request")
async def request_password_reset(
    payload: PasswordResetRequest,
    session: AsyncSession = Depends(get_session),
    request: Request = None,
):
    """Request password reset - sends email with reset link"""
    user = await user_service.get_user_by_email(session, payload.email)
    if not user:
        # Don't reveal if user exists (security best practice)
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Generate reset token
    reset_token = generate_password_reset_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Store token in database
    reset_record = PasswordResetToken(
        user_id=str(user.id),
        token=reset_token,
        expires_at=expires_at,
        ip_address=get_client_ip(request) if request else None,
        user_agent=get_user_agent(request) if request else None,
    )
    session.add(reset_record)
    await session.commit()
    
    # Send email (if email service configured)
    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
    try:
        await notification_service.send_password_reset_email(user.email, reset_link)
    except Exception:
        pass  # Email sending is optional
    
    # Log audit
    await audit_service.create_audit_log(
        session,
        AuditLogCreate(
            user_id=str(user.id),
            action_type="password_reset_request",
            resource_type="user",
            resource_id=str(user.id),
            details="Password reset requested",
            ip_address=get_client_ip(request) if request else None,
        ),
    )
    
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    payload: PasswordResetConfirm,
    session: AsyncSession = Depends(get_session),
    request: Request = None,
):
    """Confirm password reset with token"""
    from sqlalchemy import select
    
    # Find reset token
    result = await session.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == payload.token,
            PasswordResetToken.used == "false"
        )
    )
    reset_record = result.scalar_one_or_none()
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    if reset_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    # Find user
    user = await session.get(User, reset_record.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update password
    user.hashed_password = get_password_hash(payload.new_password)
    reset_record.used = "true"
    await session.commit()
    
    # Log audit
    await audit_service.create_audit_log(
        session,
        AuditLogCreate(
            user_id=str(user.id),
            action_type="password_reset_confirm",
            resource_type="user",
            resource_id=str(user.id),
            details="Password reset completed",
            ip_address=get_client_ip(request) if request else None,
        ),
    )
    
    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    request: Request = None,
):
    """Change password (requires current password)"""
    # Verify current password
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    current_user.hashed_password = get_password_hash(payload.new_password)
    await session.commit()
    
    # Log audit
    await audit_service.create_audit_log(
        session,
        AuditLogCreate(
            user_id=str(current_user.id),
            action_type="password_change",
            resource_type="user",
            resource_id=str(current_user.id),
            details="Password changed",
            ip_address=get_client_ip(request) if request else None,
        ),
    )
    
    return {"message": "Password changed successfully"}

