"""Initial tables

Revision ID: 0001_initial
Revises:
Create Date: 2025-11-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "machine",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("location", sa.String(length=255)),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("criticality", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON()),
        sa.Column("last_service_date", sa.Date()),
    )

    op.create_table(
        "modelregistry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("path", sa.String(length=255)),
        sa.Column("metadata", sa.JSON()),
    )

    op.create_table(
        "user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(length=255)),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("last_login", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "sensor",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("machine_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("sensor_type", sa.String(length=50), nullable=False),
        sa.Column("unit", sa.String(length=16)),
        sa.Column("min_threshold", sa.Numeric()),
        sa.Column("max_threshold", sa.Numeric()),
        sa.Column("warning_threshold", sa.Numeric()),
        sa.Column("critical_threshold", sa.Numeric()),
        sa.Column("metadata", sa.JSON()),
        sa.ForeignKeyConstraint(("machine_id",), ("machine.id",), ondelete="CASCADE"),
    )

    op.create_table(
        "prediction",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("sensor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("machine_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("score", sa.Numeric(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("anomaly_type", sa.String(length=64)),
        sa.Column("model_version", sa.String(length=64)),
        sa.Column("remaining_useful_life", sa.Numeric()),
        sa.Column("metadata", sa.JSON()),
        sa.ForeignKeyConstraint(("machine_id",), ("machine.id",)),
        sa.ForeignKeyConstraint(("sensor_id",), ("sensor.id",)),
    )

    op.create_table(
        "sensor_data",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("sensor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("machine_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Numeric(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON()),
        sa.ForeignKeyConstraint(("machine_id",), ("machine.id",), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(("sensor_id",), ("sensor.id",), ondelete="CASCADE"),
    )
    op.create_index("ix_sensor_data_sensor_id", "sensor_data", ["sensor_id"])
    op.create_index("ix_sensor_data_machine_id", "sensor_data", ["machine_id"])
    op.create_index("ix_sensor_data_timestamp", "sensor_data", ["timestamp"])

    op.create_table(
        "alarm",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("machine_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sensor_id", postgresql.UUID(as_uuid=True)),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True)),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("message", sa.String(length=512), nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("metadata", sa.JSON()),
        sa.ForeignKeyConstraint(("machine_id",), ("machine.id",)),
        sa.ForeignKeyConstraint(("sensor_id",), ("sensor.id",)),
        sa.ForeignKeyConstraint(("prediction_id",), ("prediction.id",)),
    )

    op.create_table(
        "ticket",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("machine_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alarm_id", postgresql.UUID(as_uuid=True)),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("assignee", sa.String(length=255)),
        sa.Column("description", sa.Text()),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("resolution_notes", sa.Text()),
        sa.Column("auto_created", sa.Boolean(), default=True),
        sa.Column("metadata", sa.JSON()),
        sa.ForeignKeyConstraint(("alarm_id",), ("alarm.id",)),
        sa.ForeignKeyConstraint(("machine_id",), ("machine.id",)),
    )


def downgrade() -> None:
    op.drop_table("ticket")
    op.drop_table("alarm")
    op.drop_index("ix_sensor_data_timestamp", table_name="sensor_data")
    op.drop_index("ix_sensor_data_machine_id", table_name="sensor_data")
    op.drop_index("ix_sensor_data_sensor_id", table_name="sensor_data")
    op.drop_table("sensor_data")
    op.drop_table("prediction")
    op.drop_table("sensor")
    op.drop_table("user")
    op.drop_table("modelregistry")
    op.drop_table("machine")

