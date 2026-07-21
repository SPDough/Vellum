"""
Phase 2 hybrid-retrieval tests: RRF fusion, filter/trust clause building,
reranker gating, and citation shaping. DB-backed hybrid SQL is exercised by the
live validation script, not here.
"""

import uuid
from unittest.mock import MagicMock

import pytest

from app.services import knowledge_retrieval_service as krs
from app.services.knowledge_retrieval_service import (
    KnowledgeRetrievalService,
    RetrievalCandidate,
    reciprocal_rank_fusion,
)


# ---------------------------------------------------------------------------
# Reciprocal rank fusion
# ---------------------------------------------------------------------------


def test_rrf_rewards_agreement_across_arms():
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    # `a` ranks top in both arms; `b` and `c` each appear once
    vector = [a, b]
    text = [a, c]
    scores = reciprocal_rank_fusion([vector, text])
    assert scores[a] > scores[b]
    assert scores[a] > scores[c]


def test_rrf_uses_rank_not_score_magnitude():
    a, b = uuid.uuid4(), uuid.uuid4()
    # Single list, `a` ahead of `b`: a must score strictly higher
    scores = reciprocal_rank_fusion([[a, b]])
    assert scores[a] > scores[b]


def test_rrf_empty_lists():
    assert reciprocal_rank_fusion([]) == {}
    assert reciprocal_rank_fusion([[], []]) == {}


def test_rrf_k_parameter_dampens_rank_gaps():
    a, b = uuid.uuid4(), uuid.uuid4()
    small_k = reciprocal_rank_fusion([[a, b]], k=1)
    large_k = reciprocal_rank_fusion([[a, b]], k=1000)
    # With larger k, the gap between rank 0 and rank 1 shrinks
    assert (small_k[a] - small_k[b]) > (large_k[a] - large_k[b])


# ---------------------------------------------------------------------------
# Filter and trust-level clause building
# ---------------------------------------------------------------------------


def test_min_trust_rejects_unknown_level():
    service = KnowledgeRetrievalService(MagicMock())
    with pytest.raises(ValueError, match="Unknown trust level"):
        service._document_filter_clause(None, "gospel")


def test_filter_clause_ignores_unfilterable_keys():
    service = KnowledgeRetrievalService(MagicMock())
    # `notes` is not a filterable field; should produce no clause
    clauses = service._document_filter_clause({"notes": "x"}, None)
    assert clauses == []


def test_filter_clause_builds_for_known_fields():
    service = KnowledgeRetrievalService(MagicMock())
    clauses = service._document_filter_clause({"domain": "custody"}, "internal_guidance")
    # one clause for domain, one for the min-trust set
    assert len(clauses) == 2


# ---------------------------------------------------------------------------
# Reranker gating
# ---------------------------------------------------------------------------


def _candidate(text: str, fused: float) -> RetrievalCandidate:
    return RetrievalCandidate(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        content=text,
        chunk_index=0,
        document_title="Doc",
        filename="doc.pdf",
        section="S",
        trust_level="authoritative",
        fused_score=fused,
    )


def test_rerank_falls_back_to_fused_order_when_unavailable(monkeypatch):
    monkeypatch.setattr(krs, "get_reranker", lambda: None)
    service = KnowledgeRetrievalService(MagicMock())
    cands = [_candidate("a", 0.9), _candidate("b", 0.1)]
    out = service._rerank("query", cands)
    assert out == cands  # unchanged order, no crash


def test_rerank_reorders_by_cross_encoder_score(monkeypatch):
    class FakeReranker:
        def score(self, query, passages):
            # Reverse the fused preference: last passage scores highest
            return [float(i) for i in range(len(passages))]

    monkeypatch.setattr(krs, "get_reranker", lambda: FakeReranker())
    service = KnowledgeRetrievalService(MagicMock())
    first, second = _candidate("a", 0.9), _candidate("b", 0.1)
    out = service._rerank("query", [first, second])
    assert out[0] is second  # reranker flipped the order
    assert out[0].rerank_score == 1.0


# ---------------------------------------------------------------------------
# Citation shaping
# ---------------------------------------------------------------------------


def test_citation_prefers_title_falls_back_to_filename():
    with_title = _candidate("x", 0.5)
    assert with_title.citation()["document_title"] == "Doc"

    no_title = _candidate("x", 0.5)
    no_title.document_title = None
    assert no_title.citation()["document_title"] == "doc.pdf"


def test_citation_includes_provenance_fields():
    cand = _candidate("x", 0.5)
    cite = cand.citation()
    assert set(cite) == {
        "document_id",
        "document_title",
        "section",
        "trust_level",
        "chunk_index",
    }
