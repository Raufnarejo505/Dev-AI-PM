"""Add audit_log, settings, webhook tables and machine thresholds

Revision ID: 0002_add_audit_settings_webhook
Revises: 0001_initial
Create Date: 2025-11-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_add_audit_settings_webhook"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add thresholds column to machine table
    op.add_column("machine", sa.Column("thresholds", postgresql.JSON(), nullable=True))

    # Create audit_log table
    op.create_table(
        "auditlog",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("user_id", sa.String(length=255), nullable=True),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
    )
    op.create_index("ix_auditlog_user_id", "auditlog", ["user_id"])
    op.create_index("ix_auditlog_action_type", "auditlog", ["action_type"])
    op.create_index("ix_auditlog_resource_type", "auditlog", ["resource_type"])
    op.create_index("ix_auditlog_created_at", "auditlog", ["created_at"])

    # Create settings table
    op.create_table(
        "settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("key", sa.String(length=128), nullable=False, unique=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("value_type", sa.String(length=32), nullable=False, server_default="string"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=False, server_default="general"),
        sa.Column("is_public", sa.Boolean(), server_default="false"),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
    )
    op.create_index("ix_settings_key", "settings", ["key"])
    op.create_index("ix_settings_category", "settings", ["category"])

    # Create webhook table
    op.create_table(
        "webhook",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("secret", sa.String(length=255), nullable=True),
        sa.Column("events", postgresql.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("headers", postgresql.JSON(), nullable=True),
        sa.Column("timeout_seconds", sa.String(length=32), server_default="5"),
        sa.Column("retry_count", sa.String(length=32), server_default="3"),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
    )

    # Update prediction table to add missing columns if needed
    try:
        op.add_column("prediction", sa.Column("prediction", sa.String(), nullable=True))
    except Exception:
        pass  # Column might already exist
    try:
        op.add_column("prediction", sa.Column("confidence", sa.Numeric(), nullable=True))
    except Exception:
        pass
    try:
        op.add_column("prediction", sa.Column("response_time_ms", sa.Numeric(), nullable=True))
    except Exception:
        pass
    try:
        op.add_column("prediction", sa.Column("contributing_features", postgresql.JSON(), nullable=True))
    except Exception:
        pass
    try:
        op.add_column("prediction", sa.Column("sensor_data_id", postgresql.UUID(as_uuid=True), nullable=True))
    except Exception:
        pass


def downgrade() -> None:
    op.drop_table("webhook")
    op.drop_index("ix_settings_category", table_name="settings")
    op.drop_index("ix_settings_key", table_name="settings")
    op.drop_table("settings")
    op.drop_index("ix_auditlog_created_at", table_name="auditlog")
    op.drop_index("ix_auditlog_resource_type", table_name="auditlog")
    op.drop_index("ix_auditlog_action_type", table_name="auditlog")
    op.drop_index("ix_auditlog_user_id", table_name="auditlog")
    op.drop_table("auditlog")
    op.drop_column("machine", "thresholds")

