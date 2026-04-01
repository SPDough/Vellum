"""
NAV RAG package: ingest, retrieve, and FastAPI integration for findings-oriented RAG.

Uses nav_rag_documents and nav_rag_chunks (see migration 003).
"""

from app.rag.retrieve import RagRetriever, RetrievalResult, RetrievedChunk
from app.rag.rag_service import (
    get_rag_retriever,
    build_explanation_prompt,
    build_rule_prompt,
    build_report_prompt,
)

__all__ = [
    "RagRetriever",
    "RetrievalResult",
    "RetrievedChunk",
    "get_rag_retriever",
    "build_explanation_prompt",
    "build_rule_prompt",
    "build_report_prompt",
]
