from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.machine import Machine
from app.schemas.machine import MachineCreate, MachineUpdate


def _prepare_payload(data: dict) -> dict:
    metadata = data.pop("metadata", None)
    if metadata is not None:
        data["metadata_json"] = metadata
    return data


async def list_machines(session: AsyncSession) -> List[Machine]:
    result = await session.execute(select(Machine).order_by(Machine.created_at.desc()))
    return result.scalars().all()


async def get_machine(session: AsyncSession, machine_id: UUID | str) -> Optional[Machine]:
    """Get machine by ID - accepts UUID or string (converts string to UUID)"""
    # Handle string IDs (for MQTT auto-registration)
    if isinstance(machine_id, str):
        try:
            machine_id = UUID(machine_id)
        except ValueError:
            # If it's not a valid UUID, try finding by name
            # Use .first() instead of scalar_one_or_none() to handle duplicates
            result = await session.execute(
                select(Machine)
                .where(Machine.name == machine_id)
                .order_by(Machine.created_at.desc())
            )
            return result.scalars().first()  # Get most recent if duplicates exist
    result = await session.execute(select(Machine).where(Machine.id == machine_id))
    return result.scalars().first()


async def create_machine(session: AsyncSession, payload: MachineCreate) -> Machine:
    machine = Machine(**_prepare_payload(payload.model_dump()))
    session.add(machine)
    await session.commit()
    await session.refresh(machine)
    return machine


async def update_machine(
    session: AsyncSession,
    machine: Machine,
    payload: MachineUpdate,
) -> Machine:
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "metadata":
            setattr(machine, "metadata_json", value)
        else:
            setattr(machine, field, value)
    await session.commit()
    await session.refresh(machine)
    return machine


async def delete_machine(session: AsyncSession, machine: Machine) -> None:
    await session.delete(machine)
    await session.commit()

