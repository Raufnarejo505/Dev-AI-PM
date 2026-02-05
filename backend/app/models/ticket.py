from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class TicketStatus(str, PyEnum):
    open = "open"
    assigned = "assigned"
    in_progress = "in_progress"
    resolved = "resolved"
    cancelled = "cancelled"


class TicketPriority(str, PyEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Ticket(Base):
    machine_id = Column(ForeignKey("machine.id"), nullable=False)
    alarm_id = Column(ForeignKey("alarm.id"), nullable=True)
    title = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False, default=TicketStatus.open.value)
    priority = Column(String(32), nullable=False, default=TicketPriority.medium.value)
    assignee = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    auto_created = Column(Boolean, default=True)
    metadata_json = Column("metadata", JSON, nullable=True)

    machine = relationship("Machine", back_populates="tickets")
    alarm = relationship("Alarm", back_populates="ticket")

