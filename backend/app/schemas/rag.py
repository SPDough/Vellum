"""Pydantic schemas for RAG document and chunk API."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RAGDocumentBase(BaseModel):
    """Base schema for RAG document."""

    filename: str
    title: Optional[str] = None
    source: Optional[str] = None
    metadata_: Optional[Dict[str, Any]] = Field(None, alias="metadata")


class RAGDocumentCreate(RAGDocumentBase):
    """Schema for creating a RAG document (e.g. after upload)."""

    filepath: str
    content_type: Optional[str] = None


class RAGDocumentUpdate(BaseModel):
    """Schema for updating RAG document metadata."""

    title: Optional[str] = None
    source: Optional[str] = None
    metadata_: Optional[Dict[str, Any]] = Field(None, alias="metadata")


class RAGDocumentResponse(BaseModel):
    """Schema for RAG document in API responses."""

    id: UUID
    filename: str
    filepath: str
    content_type: Optional[str] = None
    title: Optional[str] = None
    source: Optional[str] = None
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")
    status: str
    error_message: Optional[str] = None
    chunk_count: int
    created_at: datetime
    updated_at: datetime
    ingested_at: Optional[datetime] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class RAGChunkResponse(BaseModel):
    """Schema for a single chunk (no embedding in response by default)."""

    id: UUID
    document_id: UUID
    content: str
    chunk_index: int
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")

    model_config = {"from_attributes": True, "populate_by_name": True}


class RAGSearchResult(BaseModel):
    """A chunk returned from semantic search with similarity score."""

    chunk_id: UUID
    document_id: UUID
    filename: str
    content: str
    chunk_index: int
    score: float
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")

    model_config = {"from_attributes": True, "populate_by_name": True}


class RAGSearchRequest(BaseModel):
    """Request body for semantic search."""

    query: str
    top_k: int = Field(default=10, ge=1, le=100)
    document_ids: Optional[List[UUID]] = None  # limit search to these documents


class RAGSearchResponse(BaseModel):
    """Response for semantic search."""

    query: str
    results: List[RAGSearchResult]


# --- Hybrid knowledge search (Phase 2) ---------------------------------------


class KnowledgeSearchRequest(BaseModel):
    """Request body for hybrid knowledge search."""

    query: str
    top_k: int = Field(default=8, ge=1, le=50)
    filters: Optional[Dict[str, str]] = Field(
        default=None,
        description="Equality filters on document metadata (domain, provider, trust_level, ...)",
    )
    min_trust: Optional[str] = Field(
        default=None,
        description="Minimum trust level: draft | working_note | internal_guidance | authoritative",
    )
    use_reranker: Optional[bool] = Field(
        default=None, description="Override the server default for cross-encoder reranking"
    )


class Citation(BaseModel):
    """Provenance for a retrieved chunk."""

    document_id: UUID
    document_title: str
    section: Optional[str] = None
    trust_level: Optional[str] = None
    chunk_index: int


class KnowledgeSearchResult(BaseModel):
    """A single hybrid-search hit with fusion/rerank scores and citation."""

    chunk_id: UUID
    content: str
    citation: Citation
    vector_score: Optional[float] = None
    text_score: Optional[float] = None
    fused_score: float
    rerank_score: Optional[float] = None


class KnowledgeSearchResponse(BaseModel):
    """Response for hybrid knowledge search."""

    query: str
    reranked: bool
    results: List[KnowledgeSearchResult]


# --- Agentic knowledge lookup (Phase 3) --------------------------------------


class KnowledgeAskRequest(BaseModel):
    """Request body for an agentic knowledge question."""

    query: str
    filters: Optional[Dict[str, str]] = None
    min_trust: Optional[str] = None


class KnowledgeAskResponse(BaseModel):
    """A cited answer with routing/iteration metadata."""

    query: str
    answer: str
    route: str
    iterations: int
    citations: List[Citation]
