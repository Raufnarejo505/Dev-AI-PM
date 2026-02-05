"""Add machine state detection tables

Revision ID: 0005_add_machine_state
Revises: 0004_add_idempotency_key_to_sensor_data
Create Date: 2025-02-03 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0005_add_machine_state'
down_revision = '0004_add_idempotency_key_to_sensor_data'
branch_labels = None
depends_on = None


def upgrade():
    # Create machine_state table
    op.create_table('machine_state',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('machine_id', sa.String(length=100), nullable=False),
        sa.Column('machine_uuid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('state', sa.String(length=20), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('state_since', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False),
        sa.Column('temp_avg', sa.Float(), nullable=True),
        sa.Column('temp_spread', sa.Float(), nullable=True),
        sa.Column('d_temp_avg', sa.Float(), nullable=True),
        sa.Column('rpm_stable', sa.Float(), nullable=True),
        sa.Column('pressure_stable', sa.Float(), nullable=True),
        sa.Column('any_temp_above_min', sa.Boolean(), nullable=True, default=False),
        sa.Column('all_temps_below', sa.Boolean(), nullable=True, default=True),
        sa.Column('flags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('state_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['machine_uuid'], ['machine.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_machine_state_machine_id'), 'machine_state', ['machine_id'], unique=False)

    # Create machine_state_thresholds table
    op.create_table('machine_state_thresholds',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('machine_id', sa.String(length=100), nullable=False),
        sa.Column('machine_uuid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rpm_on', sa.Float(), nullable=True, default=5.0),
        sa.Column('rpm_prod', sa.Float(), nullable=True, default=10.0),
        sa.Column('p_on', sa.Float(), nullable=True, default=2.0),
        sa.Column('p_prod', sa.Float(), nullable=True, default=5.0),
        sa.Column('t_min_active', sa.Float(), nullable=True, default=60.0),
        sa.Column('heating_rate', sa.Float(), nullable=True, default=0.2),
        sa.Column('cooling_rate', sa.Float(), nullable=True, default=-0.2),
        sa.Column('temp_flat_rate', sa.Float(), nullable=True, default=0.2),
        sa.Column('rpm_stable_max', sa.Float(), nullable=True, default=2.0),
        sa.Column('pressure_stable_max', sa.Float(), nullable=True, default=1.0),
        sa.Column('production_enter_time', sa.Integer(), nullable=True, default=90),
        sa.Column('production_exit_time', sa.Integer(), nullable=True, default=120),
        sa.Column('state_change_debounce', sa.Integer(), nullable=True, default=60),
        sa.Column('motor_load_min', sa.Float(), nullable=True, default=0.15),
        sa.Column('throughput_min', sa.Float(), nullable=True, default=0.1),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['machine_uuid'], ['machine.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('machine_id')
    )
    op.create_index(op.f('ix_machine_state_thresholds_machine_id'), 'machine_state_thresholds', ['machine_id'], unique=False)

    # Create machine_state_transition table
    op.create_table('machine_state_transition',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('machine_id', sa.String(length=100), nullable=False),
        sa.Column('machine_uuid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('from_state', sa.String(length=20), nullable=True),
        sa.Column('to_state', sa.String(length=20), nullable=False),
        sa.Column('transition_reason', sa.String(length=200), nullable=True),
        sa.Column('transition_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('previous_state_duration', sa.Float(), nullable=True),
        sa.Column('confidence_before', sa.Float(), nullable=True),
        sa.Column('confidence_after', sa.Float(), nullable=True),
        sa.Column('sensor_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('transition_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['machine_uuid'], ['machine.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_machine_state_transition_machine_id'), 'machine_state_transition', ['machine_id'], unique=False)

    # Create machine_state_alert table
    op.create_table('machine_state_alert',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('machine_id', sa.String(length=100), nullable=False),
        sa.Column('machine_uuid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('state', sa.String(length=20), nullable=True),
        sa.Column('previous_state', sa.String(length=20), nullable=True),
        sa.Column('alert_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_acknowledged', sa.Boolean(), nullable=True, default=False),
        sa.Column('acknowledged_by', sa.String(length=100), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=True, default=False),
        sa.Column('resolved_by', sa.String(length=100), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('alert_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['machine_uuid'], ['machine.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_machine_state_alert_machine_id'), 'machine_state_alert', ['machine_id'], unique=False)

    # Create machine_process_evaluation table
    op.create_table('machine_process_evaluation',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('machine_id', sa.String(length=100), nullable=False),
        sa.Column('machine_uuid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('evaluation_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('traffic_light_status', sa.String(length=20), nullable=True),
        sa.Column('traffic_light_score', sa.Float(), nullable=True),
        sa.Column('traffic_light_reason', sa.Text(), nullable=True),
        sa.Column('baseline_deviation', sa.Float(), nullable=True),
        sa.Column('baseline_status', sa.String(length=20), nullable=True),
        sa.Column('anomaly_detected', sa.Boolean(), nullable=True, default=False),
        sa.Column('anomaly_score', sa.Float(), nullable=True),
        sa.Column('anomaly_features', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('process_efficiency', sa.Float(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('recommendations', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('evaluation_model_version', sa.String(length=50), nullable=True),
        sa.Column('evaluation_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['machine_uuid'], ['machine.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_machine_process_evaluation_machine_id'), 'machine_process_evaluation', ['machine_id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_machine_process_evaluation_machine_id'), table_name='machine_process_evaluation')
    op.drop_table('machine_process_evaluation')
    
    op.drop_index(op.f('ix_machine_state_alert_machine_id'), table_name='machine_state_alert')
    op.drop_table('machine_state_alert')
    
    op.drop_index(op.f('ix_machine_state_transition_machine_id'), table_name='machine_state_transition')
    op.drop_table('machine_state_transition')
    
    op.drop_index(op.f('ix_machine_state_thresholds_machine_id'), table_name='machine_state_thresholds')
    op.drop_table('machine_state_thresholds')
    
    op.drop_index(op.f('ix_machine_state_machine_id'), table_name='machine_state')
    op.drop_table('machine_state')
