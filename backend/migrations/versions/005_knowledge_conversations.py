"""Durable conversation memory for the knowledge agent (Phase 2).

Creates:
- the LangGraph Postgres checkpointer tables (reproducing the pinned
  langgraph-checkpoint-postgres DDL, so schema ships via Alembic rather than a
  runtime setup() call), and
- `knowledge_conversations`, the ownership/listing/TTL index keyed by thread_id.

If the langgraph checkpointer version is bumped, this migration must be
regenerated to match (see requirements.txt pin).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None

_CHECKPOINT_TABLES = [
    "checkpoint_writes",
    "checkpoint_blobs",
    "checkpoints",
    "checkpoint_migrations",
]


def upgrade() -> None:
    # 1) LangGraph checkpointer tables — run the library's own migration SQL.
    from langgraph.checkpoint.postgres import PostgresSaver

    for statement in PostgresSaver.MIGRATIONS:
        op.execute(statement)

    # 2) Conversation index table.
    op.create_table(
        "knowledge_conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("owner", sa.String(256), nullable=False),
        sa.Column("title", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("message_count", sa.Integer(), server_default="0"),
    )
    op.create_index("ix_knowledge_conversations_owner", "knowledge_conversations", ["owner"])
    op.create_index(
        "ix_knowledge_conversations_expires_at", "knowledge_conversations", ["expires_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_conversations_expires_at", table_name="knowledge_conversations")
    op.drop_index("ix_knowledge_conversations_owner", table_name="knowledge_conversations")
    op.drop_table("knowledge_conversations")
    for table in _CHECKPOINT_TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
