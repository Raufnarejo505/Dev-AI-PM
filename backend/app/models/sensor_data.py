from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, JSON, Numeric, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class SensorData(Base):
    __tablename__ = "sensor_data"

    # Override id to use BigInteger (not UUID) to match database schema
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    sensor_id = Column(ForeignKey("sensor.id", ondelete="CASCADE"), nullable=False, index=True)
    machine_id = Column(ForeignKey("machine.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    value = Column(Numeric, nullable=True)
    status = Column(String(32), nullable=False, default="normal")
    metadata_json = Column("metadata", JSON, nullable=True)

    # Note: readings and raw_payload columns don't exist in database schema
    # Removed to avoid SQL errors when querying
    # readings = Column(JSON, nullable=True)  # Not in DB
    # raw_payload = Column(JSON, nullable=True)  # Not in DB
    # ingested_at removed - not in database schema
    idempotency_key = Column(String, nullable=True, unique=True, index=True)

    sensor = relationship("Sensor", back_populates="readings")
    machine = relationship("Machine", back_populates="sensor_data")

