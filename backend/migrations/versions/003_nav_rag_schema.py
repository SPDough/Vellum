"""NAV RAG schema for ingest/retrieve (doc_type, chapter, mart_name, topics, etc.)

Used by backend/app/rag/ingest.py and retrieve.py for findings-oriented RAG.
Separate from the simple RAG tables (rag_documents/rag_chunks) to avoid schema conflict.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "nav_rag_documents",
        sa.Column("doc_id", sa.String(128), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("doc_type", sa.String(32), nullable=False),
        sa.Column("source_file", sa.String(512), nullable=False),
        sa.Column("author", sa.String(256), nullable=True),
        sa.Column("publisher", sa.String(256), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("domain", sa.String(64), nullable=True, server_default="fund_operations"),
        sa.Column("total_chunks", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("doc_id"),
    )
    op.create_index("ix_nav_rag_documents_doc_type", "nav_rag_documents", ["doc_type"])
    op.create_index("ix_nav_rag_documents_domain", "nav_rag_documents", ["domain"])

    op.create_table(
        "nav_rag_chunks",
        sa.Column("chunk_id", sa.String(256), nullable=False),
        sa.Column("doc_id", sa.String(128), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_tokens", sa.Integer(), nullable=True),
        sa.Column("chunk_seq", sa.Integer(), nullable=False),
        sa.Column("chunk_type", sa.String(32), nullable=False),
        sa.Column("chapter", sa.String(128), nullable=True),
        sa.Column("chapter_title", sa.String(256), nullable=True),
        sa.Column("section", sa.String(128), nullable=True),
        sa.Column("section_title", sa.String(256), nullable=True),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("mart_name", sa.String(128), nullable=True),
        sa.Column("topics", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("relevance_tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["doc_id"], ["nav_rag_documents.doc_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("chunk_id"),
    )
    op.create_index("ix_nav_rag_chunks_doc_id", "nav_rag_chunks", ["doc_id"])
    op.create_index("ix_nav_rag_chunks_doc_type", "nav_rag_chunks", ["chunk_type"])
    op.execute("ALTER TABLE nav_rag_chunks ADD COLUMN embedding vector(1536)")

    op.create_table(
        "rag_retrieval_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("query_text", sa.String(500), nullable=True),
        sa.Column("query_context", sa.String(64), nullable=True),
        sa.Column("top_k", sa.Integer(), nullable=True),
        sa.Column("filter_tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("chunks_returned", postgresql.JSON(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("rag_retrieval_log")
    op.drop_table("nav_rag_chunks")
    op.drop_table("nav_rag_documents")
