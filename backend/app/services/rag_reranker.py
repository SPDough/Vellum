"""
Local cross-encoder reranker for knowledge retrieval.

Wraps a sentence-transformers CrossEncoder (default bge-reranker-v2-m3) that
scores (query, passage) pairs directly, giving sharper relevance ordering than
the first-stage fused retrieval. Runs locally so chunk text never leaves the
host. Loaded lazily and cached; returns None if disabled or unavailable so the
retrieval service can fall back to the fused order without crashing.
"""

import logging
import threading
from typing import List, Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_lock = threading.Lock()
_reranker: Optional["CrossEncoderReranker"] = None
_load_failed = False


class CrossEncoderReranker:
    """Thin wrapper over a sentence-transformers CrossEncoder."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import CrossEncoder

        self.model_name = model_name
        self.model = CrossEncoder(model_name)

    def score(self, query: str, passages: List[str]) -> List[float]:
        """Return a relevance score per passage for the query (higher is better)."""
        if not passages:
            return []
        pairs = [(query, passage) for passage in passages]
        scores = self.model.predict(pairs)
        return [float(s) for s in scores]


def get_reranker() -> Optional[CrossEncoderReranker]:
    """
    Return the shared reranker, loading it on first use. Returns None if the
    model can't be loaded (e.g. sentence-transformers missing or download fails),
    which callers treat as "skip reranking".
    """
    global _reranker, _load_failed
    if _reranker is not None:
        return _reranker
    if _load_failed:
        return None
    with _lock:
        if _reranker is not None:
            return _reranker
        if _load_failed:
            return None
        try:
            _reranker = CrossEncoderReranker(settings.rag_rerank_model)
            logger.info("Loaded reranker model: %s", settings.rag_rerank_model)
        except Exception as e:  # pragma: no cover - depends on optional heavy deps
            _load_failed = True
            logger.warning("Could not load reranker %s: %s", settings.rag_rerank_model, e)
            return None
    return _reranker


def reset_reranker_cache() -> None:
    """Test helper: clear the cached reranker and failure flag."""
    global _reranker, _load_failed
    with _lock:
        _reranker = None
        _load_failed = False
