from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class AlarmStatus(str, PyEnum):
    open = "open"
    acknowledged = "acknowledged"
    resolved = "resolved"


class AlarmSeverity(str, PyEnum):
    info = "info"
    warning = "warning"
    critical = "critical"


class Alarm(Base):
    machine_id = Column(ForeignKey("machine.id"), nullable=False)
    sensor_id = Column(ForeignKey("sensor.id"), nullable=True)
    prediction_id = Column(ForeignKey("prediction.id"), nullable=True)
    severity = Column(String(32), nullable=False, default=AlarmSeverity.warning.value)
    status = Column(String(32), nullable=False, default=AlarmStatus.open.value)
    message = Column(String(512), nullable=False)
    triggered_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)

    machine = relationship("Machine", back_populates="alarms")
    sensor = relationship("Sensor", back_populates="alarms")
    prediction = relationship("Prediction", back_populates="alarm")
    ticket = relationship("Ticket", back_populates="alarm", uselist=False)

