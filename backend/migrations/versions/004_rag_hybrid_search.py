"""Hybrid search support for rag_chunks: full-text tsvector + GIN, and HNSW on embeddings.

Adds a generated tsvector column over chunk content for BM25-style keyword search
(fused with vector search via RRF in the retrieval service), plus indexes to make
both retrieval arms scalable:
  - GIN index on the tsvector for full-text search
  - HNSW index on the embedding column for approximate nearest-neighbour vector search
"""

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Full-text search column (stored, generated from content) + GIN index.
    op.execute(
        "ALTER TABLE rag_chunks "
        "ADD COLUMN IF NOT EXISTS content_tsv tsvector "
        "GENERATED ALWAYS AS (to_tsvector('english', content)) STORED"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_rag_chunks_content_tsv "
        "ON rag_chunks USING GIN (content_tsv)"
    )
    # Approximate nearest-neighbour index for vector search (cosine).
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_rag_chunks_embedding_hnsw "
        "ON rag_chunks USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_rag_chunks_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_rag_chunks_content_tsv")
    op.execute("ALTER TABLE rag_chunks DROP COLUMN IF EXISTS content_tsv")
