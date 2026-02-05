from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Numeric, String, Uuid
from sqlalchemy.orm import relationship

from app.models.base import Base


class Prediction(Base):
    sensor_id = Column(ForeignKey("sensor.id"), nullable=False)
    machine_id = Column(ForeignKey("machine.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    score = Column(Numeric, nullable=False)
    status = Column(String(32), nullable=False)
    anomaly_type = Column(String(64), nullable=True)
    model_version = Column(String(64), nullable=True)
    rul = Column("remaining_useful_life", Integer, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)

    prediction = Column(String, nullable=True)
    confidence = Column(Numeric, nullable=True)
    response_time_ms = Column(Numeric, nullable=True)
    contributing_features = Column(JSON, nullable=True)
    sensor_data_id = Column(Uuid(as_uuid=True), ForeignKey("sensor_data.id"), nullable=True)

    sensor = relationship("Sensor", back_populates="predictions")
    machine = relationship("Machine", back_populates="predictions")
    alarm = relationship("Alarm", back_populates="prediction", uselist=False)
    sensor_data = relationship("SensorData", backref="predictions")

