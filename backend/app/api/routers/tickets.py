from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_current_user
from app.models.user import User
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.ticket import TicketCreate, TicketRead, TicketUpdate
from app.schemas.comment import CommentCreate, CommentRead
from app.services import ticket_service, comment_service

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=List[TicketRead])
async def list_tickets(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(Ticket).order_by(Ticket.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
async def create_ticket(payload: TicketCreate, session: AsyncSession = Depends(get_session)):
    return await ticket_service.create_ticket(session, payload)


@router.patch("/{ticket_id}", response_model=TicketRead)
async def update_ticket(ticket_id: UUID, payload: TicketUpdate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return await ticket_service.update_ticket(session, ticket, payload)


@router.post("/{ticket_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def create_ticket_comment(
    ticket_id: UUID,
    payload: CommentCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Add a comment to a ticket"""
    # Verify ticket exists
    result = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    comment_data = CommentCreate(
        resource_type="ticket",
        resource_id=str(ticket_id),
        content=payload.content,
        is_internal=payload.is_internal,
    )
    return await comment_service.create_comment(session, comment_data, str(current_user.id))


@router.get("/{ticket_id}/comments", response_model=List[CommentRead])
async def get_ticket_comments(
    ticket_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get all comments for a ticket"""
    # Verify ticket exists
    result = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return await comment_service.get_comments(session, "ticket", str(ticket_id))

