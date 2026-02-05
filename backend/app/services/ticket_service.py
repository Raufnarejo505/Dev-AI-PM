from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alarm import Alarm
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate, TicketUpdate


def _prepare_payload(data: dict) -> dict:
    metadata = data.pop("metadata", None)
    if metadata is not None:
        data["metadata_json"] = metadata
    return data


async def create_ticket(session: AsyncSession, payload: TicketCreate) -> Ticket:
    ticket = Ticket(**_prepare_payload(payload.model_dump()))
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket


async def ensure_ticket_for_alarm(session: AsyncSession, alarm: Alarm) -> Ticket:
    result = await session.execute(select(Ticket).where(Ticket.alarm_id == alarm.id))
    ticket = result.scalars().first()
    if ticket:
        return ticket

    payload = TicketCreate(
        machine_id=alarm.machine_id,
        alarm_id=alarm.id,
        title=f"Alarm {alarm.severity.upper()} - {alarm.message[:40]}",
        priority="critical" if alarm.severity == "critical" else "high",
        assignee="maintenance@factory.local",
        description=alarm.message,
        due_at=datetime.now(timezone.utc) + timedelta(hours=4),
        auto_created=True,
        metadata={"alarm_severity": alarm.severity},
    )
    return await create_ticket(session, payload)


async def update_ticket(session: AsyncSession, ticket: Ticket, payload: TicketUpdate) -> Ticket:
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "metadata":
            setattr(ticket, "metadata_json", value)
        else:
            setattr(ticket, field, value)
    await session.commit()
    await session.refresh(ticket)
    return ticket

