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
