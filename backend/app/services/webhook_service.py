import asyncio
import json
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import Webhook
from app.schemas.webhook import WebhookCreate, WebhookUpdate


async def get_webhook(session: AsyncSession, webhook_id: UUID) -> Optional[Webhook]:
    """Get a webhook by ID"""
    result = await session.execute(select(Webhook).where(Webhook.id == webhook_id))
    return result.scalar_one_or_none()


async def get_webhooks(
    session: AsyncSession,
    is_active: Optional[bool] = None,
) -> List[Webhook]:
    """Get all webhooks, optionally filtered by active status"""
    query = select(Webhook)
    if is_active is not None:
        query = query.where(Webhook.is_active == is_active)
    result = await session.execute(query)
    return list(result.scalars().all())


async def create_webhook(session: AsyncSession, webhook_data: WebhookCreate) -> Webhook:
    """Create a new webhook"""
    webhook = Webhook(**webhook_data.model_dump())
    session.add(webhook)
    await session.commit()
    await session.refresh(webhook)
    return webhook


async def update_webhook(
    session: AsyncSession,
    webhook: Webhook,
    webhook_data: WebhookUpdate,
) -> Webhook:
    """Update an existing webhook"""
    update_data = webhook_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(webhook, key, value)
    await session.commit()
    await session.refresh(webhook)
    return webhook


async def delete_webhook(session: AsyncSession, webhook: Webhook) -> None:
    """Delete a webhook"""
    await session.delete(webhook)
    await session.commit()


async def trigger_webhook(webhook: Webhook, event_type: str, payload: Dict[str, Any]) -> bool:
    """Trigger a webhook if it's active and subscribed to the event"""
    if not webhook.is_active:
        return False
    
    if event_type not in webhook.events:
        return False
    
    try:
        headers = webhook.headers or {}
        headers["Content-Type"] = "application/json"
        
        webhook_payload = {
            "event": event_type,
            "timestamp": payload.get("timestamp"),
            "data": payload,
        }
        
        timeout = float(webhook.timeout_seconds or "5")
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                webhook.url,
                json=webhook_payload,
                headers=headers,
            )
            return response.is_success
    except Exception:
        return False

