"""
RAG (Retrieval-Augmented Generation) database models.

Stores document metadata and chunked content with vector embeddings
for semantic search. Uses pgvector for similarity search.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import DeclarativeBase, relationship

from pgvector.sqlalchemy import Vector

# Default embedding dimension (OpenAI text-embedding-3-small; override via RAG_EMBEDDING_DIMENSION)
DEFAULT_EMBEDDING_DIMENSION = 1536


class Base(DeclarativeBase):
    """Declarative base for RAG models."""

    pass


class RAGDocument(Base):
    """Source document metadata for RAG ingestion."""

    __tablename__ = "rag_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Storage and identity
    filename = Column(String(512), nullable=False, index=True)
    filepath = Column(String(1024), nullable=False)  # path on server or blob URL
    content_type = Column(String(128), nullable=True)  # e.g. application/pdf, text/plain
    # Optional metadata
    title = Column(String(512), nullable=True, index=True)
    source = Column(String(256), nullable=True)  # e.g. "upload", "s3", "sharepoint"
    metadata_ = Column("metadata", JSON, default=dict)  # arbitrary metadata
    # Ingestion state
    status = Column(String(32), nullable=False, default="pending", index=True)
    # pending | ingesting | completed | failed
    error_message = Column(Text, nullable=True)  # if status == failed
    chunk_count = Column(Integer, default=0)
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ingested_at = Column(DateTime, nullable=True)

    chunks = relationship("RAGChunk", back_populates="document", cascade="all, delete-orphan")


class RAGChunk(Base):
    """A chunk of document text with its vector embedding for semantic search."""

    __tablename__ = "rag_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rag_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Chunk content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # order within document
    # Optional chunk-level metadata (e.g. page number for PDF)
    metadata_ = Column("metadata", JSON, default=dict)
    # Vector embedding; dimension must match embedding model (e.g. 1536 for OpenAI)
    embedding = Column(Vector(DEFAULT_EMBEDDING_DIMENSION), nullable=True)

    document = relationship("RAGDocument", back_populates="chunks")
