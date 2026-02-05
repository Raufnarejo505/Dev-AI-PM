"""Add idempotency_key column to sensor_data

Revision ID: 0004_add_idempotency_key_to_sensor_data
Revises: 0003_auth_enhance
Create Date: 2025-12-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_add_idempotency_key_to_sensor_data"
down_revision = "0003_auth_enhance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make migration idempotent: only add column/index if they don't already exist
    op.execute(
        """
        ALTER TABLE sensor_data
        ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_sensor_data_idempotency_key
        ON sensor_data(idempotency_key)
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP INDEX IF EXISTS ix_sensor_data_idempotency_key"
    )
    op.execute(
        "ALTER TABLE sensor_data DROP COLUMN IF EXISTS idempotency_key"
    )


