"""RAG documents and chunks with pgvector

Revision ID: 002
Revises: 001
Create Date: 2025-03-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "rag_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("filepath", sa.String(1024), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=True),
        sa.Column("title", sa.String(512), nullable=True),
        sa.Column("source", sa.String(256), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column("ingested_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rag_documents_filename", "rag_documents", ["filename"])
    op.create_index("ix_rag_documents_title", "rag_documents", ["title"])
    op.create_index("ix_rag_documents_status", "rag_documents", ["status"])

    op.create_table(
        "rag_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["rag_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rag_chunks_document_id", "rag_chunks", ["document_id"])
    # pgvector column (1536 = OpenAI text-embedding-3-small dimension)
    op.execute("ALTER TABLE rag_chunks ADD COLUMN embedding vector(1536)")


def downgrade() -> None:
    op.drop_table("rag_chunks")
    op.drop_table("rag_documents")
