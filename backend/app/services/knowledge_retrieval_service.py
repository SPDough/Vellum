"""
Knowledge retrieval service: hybrid search over the RAG chunk store.

Combines dense vector search (pgvector cosine) with sparse full-text search
(Postgres tsvector) via reciprocal rank fusion, applies metadata-contract
filters, and optionally reranks the fused candidates with a local cross-encoder.
Returns citation-bearing results (document title, section, trust level).

Authority note: retrieval is assistive. Results here inform explanation and
workflow guidance; they never override deterministic rules or control logic.
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fastapi import Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_sync_db
from app.models.rag import RAGChunk, RAGDocument
from app.services.embedding_service import embedding_service
from app.services.rag_reranker import get_reranker

logger = logging.getLogger(__name__)
settings = get_settings()

# Metadata fields on the parent document that can be used as retrieval filters.
FILTERABLE_FIELDS = (
    "domain",
    "provider",
    "source_type",
    "document_type",
    "trust_level",
    "asset_class",
    "business_process",
)

# Trust levels ordered from most to least authoritative (for min-trust filtering).
_TRUST_ORDER = ["draft", "working_note", "internal_guidance", "authoritative"]


@dataclass
class RetrievalCandidate:
    """A single retrieved chunk with provenance for citation."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    content: str
    chunk_index: int
    document_title: Optional[str]
    filename: str
    section: Optional[str]
    trust_level: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Scores from each arm (None if not retrieved by that arm) and the fused/final score.
    vector_score: Optional[float] = None
    text_score: Optional[float] = None
    fused_score: float = 0.0
    rerank_score: Optional[float] = None

    def citation(self) -> Dict[str, Any]:
        """Compact provenance for surfacing alongside an answer."""
        return {
            "document_id": str(self.document_id),
            "document_title": self.document_title or self.filename,
            "section": self.section,
            "trust_level": self.trust_level,
            "chunk_index": self.chunk_index,
        }


def reciprocal_rank_fusion(
    ranked_lists: Sequence[Sequence[uuid.UUID]], k: int = 60
) -> Dict[uuid.UUID, float]:
    """
    Fuse multiple ranked id lists into a single score map via reciprocal rank fusion.

    RRF score for an item = sum over lists of 1 / (k + rank), rank being 0-based
    position in that list. Robust to the two arms using incomparable score scales.
    """
    scores: Dict[uuid.UUID, float] = {}
    for ranked in ranked_lists:
        for rank, item_id in enumerate(ranked):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
    return scores


class KnowledgeRetrievalService:
    """Hybrid retrieval over rag_chunks with optional reranking."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _document_filter_clause(self, filters: Optional[Dict[str, str]], min_trust: Optional[str]):
        """Build SQLAlchemy where-clauses from metadata filters and a minimum trust level."""
        clauses = []
        for key, value in (filters or {}).items():
            if key in FILTERABLE_FIELDS and value is not None:
                clauses.append(RAGDocument.metadata_[key].astext == value)
        if min_trust:
            if min_trust not in _TRUST_ORDER:
                raise ValueError(f"Unknown trust level: {min_trust}")
            allowed = _TRUST_ORDER[_TRUST_ORDER.index(min_trust) :]
            clauses.append(RAGDocument.metadata_["trust_level"].astext.in_(allowed))
        return clauses

    def _vector_search(
        self, query_embedding: List[float], limit: int, filter_clauses
    ) -> List[Tuple[uuid.UUID, float]]:
        q = (
            select(
                RAGChunk.id,
                (1 - RAGChunk.embedding.cosine_distance(query_embedding)).label("score"),
            )
            .join(RAGDocument, RAGChunk.document_id == RAGDocument.id)
            .where(RAGChunk.embedding.isnot(None))
        )
        for clause in filter_clauses:
            q = q.where(clause)
        q = q.order_by(RAGChunk.embedding.cosine_distance(query_embedding)).limit(limit)
        return [(r.id, float(r.score)) for r in self.db.execute(q).all()]

    def _text_search(
        self, query: str, limit: int, filter_clauses
    ) -> List[Tuple[uuid.UUID, float]]:
        tsquery = func.websearch_to_tsquery("english", query)
        content_tsv = RAGChunk.__table__.c.content_tsv
        q = (
            select(RAGChunk.id, func.ts_rank(content_tsv, tsquery).label("score"))
            .join(RAGDocument, RAGChunk.document_id == RAGDocument.id)
            .where(content_tsv.op("@@")(tsquery))
        )
        for clause in filter_clauses:
            q = q.where(clause)
        q = q.order_by(text("score DESC")).limit(limit)
        return [(r.id, float(r.score)) for r in self.db.execute(q).all()]

    def _load_candidates(
        self, chunk_ids: List[uuid.UUID]
    ) -> Dict[uuid.UUID, RetrievalCandidate]:
        if not chunk_ids:
            return {}
        q = (
            select(
                RAGChunk.id,
                RAGChunk.document_id,
                RAGChunk.content,
                RAGChunk.chunk_index,
                RAGChunk.metadata_,
                RAGDocument.title,
                RAGDocument.filename,
                RAGDocument.metadata_.label("doc_metadata"),
            )
            .join(RAGDocument, RAGChunk.document_id == RAGDocument.id)
            .where(RAGChunk.id.in_(chunk_ids))
        )
        out: Dict[uuid.UUID, RetrievalCandidate] = {}
        for r in self.db.execute(q).all():
            chunk_meta = r.metadata_ or {}
            doc_meta = r.doc_metadata or {}
            out[r.id] = RetrievalCandidate(
                chunk_id=r.id,
                document_id=r.document_id,
                content=r.content,
                chunk_index=r.chunk_index,
                document_title=r.title,
                filename=r.filename,
                section=chunk_meta.get("section"),
                trust_level=doc_meta.get("trust_level"),
                metadata=chunk_meta,
            )
        return out

    async def search(
        self,
        query: str,
        *,
        top_k: int = 8,
        candidate_pool: int = 40,
        filters: Optional[Dict[str, str]] = None,
        min_trust: Optional[str] = None,
        use_reranker: Optional[bool] = None,
    ) -> List[RetrievalCandidate]:
        """
        Hybrid search: vector + full-text retrieval fused with RRF, optionally
        reranked, returning the top_k citation-bearing candidates.

        candidate_pool bounds how many rows each arm contributes before fusion
        (and how many the reranker scores).
        """
        query_embedding = await embedding_service.get_embedding(query)
        filter_clauses = self._document_filter_clause(filters, min_trust)

        vector_hits = self._vector_search(query_embedding, candidate_pool, filter_clauses)
        text_hits = self._text_search(query, candidate_pool, filter_clauses)

        vector_scores = {cid: s for cid, s in vector_hits}
        text_scores = {cid: s for cid, s in text_hits}
        fused = reciprocal_rank_fusion(
            [[cid for cid, _ in vector_hits], [cid for cid, _ in text_hits]]
        )
        if not fused:
            return []

        candidates = self._load_candidates(list(fused.keys()))
        for cid, cand in candidates.items():
            cand.vector_score = vector_scores.get(cid)
            cand.text_score = text_scores.get(cid)
            cand.fused_score = fused[cid]

        ordered = sorted(candidates.values(), key=lambda c: c.fused_score, reverse=True)

        enabled = settings.rag_rerank_enabled if use_reranker is None else use_reranker
        if enabled:
            ordered = self._rerank(query, ordered)

        return ordered[:top_k]

    def _rerank(
        self, query: str, candidates: List[RetrievalCandidate]
    ) -> List[RetrievalCandidate]:
        reranker = get_reranker()
        if reranker is None:
            logger.warning("Reranking requested but reranker unavailable; using fused order")
            return candidates
        scored = reranker.score(query, [c.content for c in candidates])
        for cand, score in zip(candidates, scored):
            cand.rerank_score = score
        return sorted(candidates, key=lambda c: c.rerank_score, reverse=True)


def get_knowledge_retrieval_service(
    db: Session = Depends(get_sync_db),
) -> KnowledgeRetrievalService:
    """Dependency: return knowledge retrieval service."""
    return KnowledgeRetrievalService(db)
