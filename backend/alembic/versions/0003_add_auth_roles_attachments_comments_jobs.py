"""Add auth enhancements, roles, attachments, comments, jobs

Revision ID: 0003_auth_enhance
Revises: 0002_add_audit_settings_webhook
Create Date: 2025-11-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_auth_enhance"
down_revision = "0002_add_audit_settings_webhook"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add refresh token columns to user table
    op.add_column("user", sa.Column("refresh_token_hash", sa.String(length=255), nullable=True))
    op.add_column("user", sa.Column("refresh_token_expires_at", sa.DateTime(timezone=True), nullable=True))
    
    # Create password_reset_token table
    op.create_table(
        "passwordresettoken",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.String(length=32), server_default="false"),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
    )
    op.create_index("ix_passwordresettoken_user_id", "passwordresettoken", ["user_id"])
    op.create_index("ix_passwordresettoken_token", "passwordresettoken", ["token"])

    # Create role table
    op.create_table(
        "role",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("name", sa.String(length=64), nullable=False, unique=True),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("permissions", postgresql.JSON(), nullable=False),
        sa.Column("is_system", sa.String(length=32), server_default="false"),
    )
    op.create_index("ix_role_name", "role", ["name"])

    # Create attachment table
    op.create_table(
        "attachment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("uploaded_by", sa.String(length=255), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
    )

    # Create comment table
    op.create_table(
        "comment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_internal", sa.String(length=32), server_default="false"),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
    )
    op.create_index("ix_comment_resource_id", "comment", ["resource_id"])

    # Create job table
    op.create_table(
        "job",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("progress", sa.Integer(), server_default="0"),
        sa.Column("result", postgresql.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
    )
    op.create_index("ix_job_job_type", "job", ["job_type"])


def downgrade() -> None:
    op.drop_index("ix_job_job_type", table_name="job")
    op.drop_table("job")
    op.drop_index("ix_comment_resource_id", table_name="comment")
    op.drop_table("comment")
    op.drop_table("attachment")
    op.drop_index("ix_role_name", table_name="role")
    op.drop_table("role")
    op.drop_index("ix_passwordresettoken_token", table_name="passwordresettoken")
    op.drop_index("ix_passwordresettoken_user_id", table_name="passwordresettoken")
    op.drop_table("passwordresettoken")
    # Remove refresh token columns from user table
    op.drop_column("user", "refresh_token_expires_at")
    op.drop_column("user", "refresh_token_hash")

