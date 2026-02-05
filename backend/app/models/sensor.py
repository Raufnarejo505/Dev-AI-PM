from sqlalchemy import JSON, Column, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class Sensor(Base):
    machine_id = Column(ForeignKey("machine.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    sensor_type = Column(String(50), nullable=False)
    unit = Column(String(16), nullable=True)
    min_threshold = Column(Numeric, nullable=True)
    max_threshold = Column(Numeric, nullable=True)
    warning_threshold = Column(Numeric, nullable=True)
    critical_threshold = Column(Numeric, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)

    machine = relationship("Machine", back_populates="sensors")
    readings = relationship("SensorData", back_populates="sensor")
    predictions = relationship("Prediction", back_populates="sensor")
    alarms = relationship("Alarm", back_populates="sensor")

