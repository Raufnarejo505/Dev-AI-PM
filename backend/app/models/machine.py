from enum import Enum as PyEnum

from sqlalchemy import JSON, Column, Date, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class MachineStatus(str, PyEnum):
    online = "online"
    maintenance = "maintenance"
    offline = "offline"
    degraded = "degraded"


class Machine(Base):
    name = Column(String(100), unique=True, nullable=False)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default=MachineStatus.online.value)
    criticality = Column(String(32), nullable=False, default="medium")
    metadata_json = Column("metadata", JSON, nullable=True)
    last_service_date = Column(Date, nullable=True)
    # Thresholds for machine-level monitoring
    thresholds_json = Column("thresholds", JSON, nullable=True)  # {"temperature": {"warning": 70, "critical": 85}, ...}

    sensors = relationship("Sensor", back_populates="machine", cascade="all, delete-orphan")
    sensor_data = relationship("SensorData", back_populates="machine")
    predictions = relationship("Prediction", back_populates="machine")
    alarms = relationship("Alarm", back_populates="machine")
    tickets = relationship("Ticket", back_populates="machine")
    
    # Machine state relationships
    states = relationship("MachineState", back_populates="machine")
    state_thresholds = relationship("MachineStateThresholds", back_populates="machine")
    state_alerts = relationship("MachineStateAlert", back_populates="machine")

