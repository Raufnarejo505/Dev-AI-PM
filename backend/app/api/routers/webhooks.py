from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_current_user, require_admin, require_engineer
from app.models.user import User
from app.schemas.webhook import WebhookCreate, WebhookRead, WebhookUpdate
from app.services import webhook_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("", response_model=List[WebhookRead])
async def list_webhooks(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_engineer),
    is_active: bool = None,
):
    """List all webhooks"""
    return await webhook_service.get_webhooks(session, is_active=is_active)


@router.post("", response_model=WebhookRead, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    payload: WebhookCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Create a new webhook (admin only)"""
    return await webhook_service.create_webhook(session, payload)


@router.get("/{webhook_id}", response_model=WebhookRead)
async def get_webhook(
    webhook_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_engineer),
):
    """Get a webhook by ID"""
    webhook = await webhook_service.get_webhook(session, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@router.patch("/{webhook_id}", response_model=WebhookRead)
async def update_webhook(
    webhook_id: UUID,
    payload: WebhookUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Update a webhook (admin only)"""
    webhook = await webhook_service.get_webhook(session, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return await webhook_service.update_webhook(session, webhook, payload)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Delete a webhook (admin only)"""
    webhook = await webhook_service.get_webhook(session, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await webhook_service.delete_webhook(session, webhook)

