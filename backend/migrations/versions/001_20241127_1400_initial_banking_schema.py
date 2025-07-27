"""Initial banking schema

Revision ID: 001
Revises: 
Create Date: 2024-11-27 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial banking schema"""
    
    # Create audit schema for compliance
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('position', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('auth_provider', sa.String(50), nullable=False, default='simple'),
        sa.Column('external_id', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    
    # Indexes for users
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_role', 'users', ['role'])
    op.create_index('ix_users_department', 'users', ['department'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    
    # SOP Documents table
    op.create_table(
        'sop_documents',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('document_number', sa.String(50), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('subcategory', sa.String(100), nullable=True),
        sa.Column('process_type', sa.String(50), nullable=False),
        sa.Column('business_area', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(255), nullable=False),
        sa.Column('last_reviewed', sa.DateTime(), nullable=True),
        sa.Column('review_frequency_days', sa.Integer(), nullable=False, default=365),
        sa.Column('status', sa.String(20), nullable=False, default='ACTIVE'),
        sa.Column('is_automated', sa.Boolean(), nullable=False, default=False),
        sa.Column('automation_percentage', sa.Float(), nullable=False, default=0.0),
        sa.Column('embeddings', postgresql.JSON(), nullable=True),
        sa.Column('neo4j_node_id', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_number')
    )
    
    # Indexes for SOP documents
    op.create_index('ix_sop_documents_title', 'sop_documents', ['title'])
    op.create_index('ix_sop_documents_category', 'sop_documents', ['category'])
    op.create_index('ix_sop_documents_business_area', 'sop_documents', ['business_area'])
    op.create_index('ix_sop_documents_process_type', 'sop_documents', ['process_type'])
    op.create_index('ix_sop_documents_status', 'sop_documents', ['status'])
    
    # SOP Steps table
    op.create_table(
        'sop_steps',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('sop_document_id', sa.String(36), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('step_title', sa.String(255), nullable=False),
        sa.Column('step_description', sa.Text(), nullable=False),
        sa.Column('is_manual', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_automated', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_decision_point', sa.Boolean(), nullable=False, default=False),
        sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('automation_tool', sa.String(100), nullable=True),
        sa.Column('automation_confidence', sa.Float(), nullable=True),
        sa.Column('depends_on_steps', postgresql.JSON(), nullable=True),
        sa.Column('prerequisite_data', postgresql.JSON(), nullable=True),
        sa.Column('neo4j_relationships', postgresql.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['sop_document_id'], ['sop_documents.id'], ondelete='CASCADE')
    )
    
    # Indexes for SOP steps
    op.create_index('ix_sop_steps_sop_document_id', 'sop_steps', ['sop_document_id'])
    op.create_index('ix_sop_steps_step_number', 'sop_steps', ['step_number'])
    
    # SOP Executions table
    op.create_table(
        'sop_executions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('sop_document_id', sa.String(36), nullable=False),
        sa.Column('execution_name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='NOT_STARTED'),
        sa.Column('initiated_by', sa.String(255), nullable=False),
        sa.Column('assigned_to', sa.String(255), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('actual_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('context_data', postgresql.JSON(), nullable=True),
        sa.Column('input_parameters', postgresql.JSON(), nullable=True),
        sa.Column('final_output', postgresql.JSON(), nullable=True),
        sa.Column('current_step_id', sa.String(36), nullable=True),
        sa.Column('completed_steps', postgresql.JSON(), nullable=True),
        sa.Column('failed_steps', postgresql.JSON(), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), nullable=False, default=False),
        sa.Column('approval_status', sa.String(20), nullable=True),
        sa.Column('approval_notes', sa.Text(), nullable=True),
        sa.Column('approved_by', sa.String(255), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('execution_log', postgresql.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['sop_document_id'], ['sop_documents.id'])
    )
    
    # Indexes for SOP executions
    op.create_index('ix_sop_executions_sop_document_id', 'sop_executions', ['sop_document_id'])
    op.create_index('ix_sop_executions_status', 'sop_executions', ['status'])
    op.create_index('ix_sop_executions_initiated_by', 'sop_executions', ['initiated_by'])
    op.create_index('ix_sop_executions_created_at', 'sop_executions', ['created_at'])
    
    # Trades table
    op.create_table(
        'trades',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('trade_id', sa.String(50), nullable=False),
        sa.Column('external_trade_id', sa.String(100), nullable=True),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('instrument_type', sa.String(20), nullable=False, default='EQUITY'),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(15, 6), nullable=False),
        sa.Column('side', sa.String(10), nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('settlement_date', sa.Date(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('counterparty', sa.String(100), nullable=False),
        sa.Column('account', sa.String(50), nullable=False),
        sa.Column('portfolio', sa.String(50), nullable=True),
        sa.Column('trader_id', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='NEW'),
        sa.Column('trade_time', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('settlement_instructions', postgresql.JSON(), nullable=True),
        sa.Column('compliance_checks', postgresql.JSON(), nullable=True),
        sa.Column('risk_metrics', postgresql.JSON(), nullable=True),
        sa.Column('audit_trail', postgresql.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('trade_id')
    )
    
    # Indexes for trades
    op.create_index('ix_trades_trade_id', 'trades', ['trade_id'])
    op.create_index('ix_trades_symbol', 'trades', ['symbol'])
    op.create_index('ix_trades_trade_date', 'trades', ['trade_date'])
    op.create_index('ix_trades_settlement_date', 'trades', ['settlement_date'])
    op.create_index('ix_trades_status', 'trades', ['status'])
    op.create_index('ix_trades_counterparty', 'trades', ['counterparty'])
    op.create_index('ix_trades_account', 'trades', ['account'])
    
    # Audit Log table (in audit schema for compliance)
    op.create_table(
        'audit_log',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('details', postgresql.JSON(), nullable=True),
        sa.Column('before_state', postgresql.JSON(), nullable=True),
        sa.Column('after_state', postgresql.JSON(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('data_hash', sa.String(64), nullable=True),  # For integrity verification
        sa.PrimaryKeyConstraint('id'),
        schema='audit'
    )
    
    # Indexes for audit log (critical for performance in compliance reporting)
    op.create_index('ix_audit_log_user_id', 'audit_log', ['user_id'], schema='audit')
    op.create_index('ix_audit_log_action', 'audit_log', ['action'], schema='audit')
    op.create_index('ix_audit_log_timestamp', 'audit_log', ['timestamp'], schema='audit')
    op.create_index('ix_audit_log_resource_type', 'audit_log', ['resource_type'], schema='audit')
    op.create_index('ix_audit_log_resource_id', 'audit_log', ['resource_id'], schema='audit')
    
    # Data sandbox records table
    op.create_table(
        'data_records',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('data_type', sa.String(50), nullable=False),
        sa.Column('data', postgresql.JSON(), nullable=False),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for data records
    op.create_index('ix_data_records_timestamp', 'data_records', ['timestamp'])
    op.create_index('ix_data_records_source', 'data_records', ['source'])
    op.create_index('ix_data_records_data_type', 'data_records', ['data_type'])
    
    # Create triggers for updated_at columns
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Apply triggers to tables with updated_at columns
    for table in ['users', 'sop_documents', 'sop_executions', 'trades']:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at 
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    """Drop all tables and schemas"""
    
    # Drop triggers first
    for table in ['users', 'sop_documents', 'sop_executions', 'trades']:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")
    
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop tables
    op.drop_table('data_records')
    op.drop_table('audit_log', schema='audit')
    op.drop_table('trades')
    op.drop_table('sop_executions')
    op.drop_table('sop_steps')
    op.drop_table('sop_documents')
    op.drop_table('users')
    
    # Drop audit schema
    op.execute("DROP SCHEMA IF EXISTS audit CASCADE")