"""
Alembic environment configuration for Otomeshon Banking Platform
"""

import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.core.database import Base

# Import all models to ensure they're registered with SQLAlchemy
from app.models.user import User
from app.models.sop import SOPDocument, SOPStep, SOPExecution, SOPStepExecution
from app.models.trade import Trade, TradeExecution, Position
from app.models.workflow import WorkflowDefinition, WorkflowInstance, WorkflowStep
from app.models.data_sandbox import DataRecord, DataStream
from app.models.knowledge_graph import KnowledgeNode, KnowledgeRelation
from app.models.procedure_document_row import ProcedureDocumentRow  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url():
    """Get database URL from settings"""
    try:
        settings = get_settings()
        return settings.database_url
    except Exception:
        # Fallback for environments where config isn't available
        return os.getenv("DATABASE_URL", "postgresql://app:changeme@localhost:5432/otomeshon")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Banking-specific configuration
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        # Version table in separate schema for banking compliance
        version_table_schema="audit"
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Override sqlalchemy.url in alembic config
    config.set_main_option("sqlalchemy.url", get_database_url())

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Banking-specific configuration
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
            # Version table in separate schema for banking compliance
            version_table_schema="audit",
            # Include indexes in autogenerate
            include_name=lambda name, type_, parent_names: True,
            # Custom naming convention for constraints
            render_as_batch=True,  # For SQLite compatibility in tests
        )

        with context.begin_transaction():
            context.run_migrations()


# Create audit schema if it doesn't exist
def create_audit_schema():
    """Create audit schema for banking compliance"""
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(get_database_url())

        with engine.connect() as conn:
            # Create audit schema if it doesn't exist
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS audit"))
            conn.commit()
    except Exception as e:
        print(f"Warning: Could not create audit schema: {e}")


if context.is_offline_mode():
    run_migrations_offline()
else:
    create_audit_schema()
    run_migrations_online()