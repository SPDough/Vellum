"""
Otomeshon RAG retrieval — redirect to backend package.

Use: from app.rag.retrieve import RagRetriever, RetrievalResult, RetrievedChunk

Ensure backend is on PYTHONPATH (e.g. PYTHONPATH=backend when running).
"""
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.join(_REPO_ROOT, "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# Re-export for "from retrieve import ..." when run from repo root
from app.rag.retrieve import (
    RagRetriever,
    RetrievalResult,
    RetrievedChunk,
    FINDING_QUERIES,
    RetrievalPurpose,
)

__all__ = [
    "RagRetriever",
    "RetrievalResult",
    "RetrievedChunk",
    "FINDING_QUERIES",
    "RetrievalPurpose",
]
