"""
Phase 1 knowledge-ingestion tests: metadata contract enforcement,
structure-aware chunking, loader routing/fallback, and enrichment gating.
"""

import json
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.endpoints import rag
from app.core.config import get_settings
from app.core.database import get_sync_db
from app.schemas.rag_metadata import KnowledgeDocumentMetadata
from app.services import rag_pipeline_service as pipeline

VALID_METADATA = {
    "title": "State Street Custody Accounting API Listing",
    "source_type": "custodian_api_spec",
    "domain": "custody",
    "provider": "state_street",
    "document_type": "spreadsheet_extract",
    "effective_date": "2026-02-14",
    "trust_level": "authoritative",
    "tags": ["api", "custody"],
}


# ---------------------------------------------------------------------------
# Metadata contract schema
# ---------------------------------------------------------------------------


def test_contract_accepts_valid_example():
    contract = KnowledgeDocumentMetadata.model_validate(VALID_METADATA)
    stored = contract.to_document_metadata()
    assert stored["trust_level"] == "authoritative"
    assert stored["effective_date"] == "2026-02-14"


def test_contract_rejects_missing_trust_level():
    metadata = {k: v for k, v in VALID_METADATA.items() if k != "trust_level"}
    with pytest.raises(ValidationError, match="trust_level"):
        KnowledgeDocumentMetadata.model_validate(metadata)


def test_contract_rejects_unknown_domain():
    metadata = {**VALID_METADATA, "domain": "astrology"}
    with pytest.raises(ValidationError, match="domain"):
        KnowledgeDocumentMetadata.model_validate(metadata)


def test_contract_allows_extra_fields():
    metadata = {**VALID_METADATA, "custom_key": "custom_value"}
    contract = KnowledgeDocumentMetadata.model_validate(metadata)
    assert contract.to_document_metadata()["custom_key"] == "custom_value"


def test_contract_rejects_blank_tags():
    metadata = {**VALID_METADATA, "tags": ["api", "  "]}
    with pytest.raises(ValidationError, match="tags"):
        KnowledgeDocumentMetadata.model_validate(metadata)


# ---------------------------------------------------------------------------
# Structure-aware chunking
# ---------------------------------------------------------------------------

MARKDOWN_FIXTURE = """# Fixed income accruals

Intro paragraph on accrual conventions.

## Mezzanine tranches

Mezzanine bonds accrue interest per the subordination waterfall.

### Payment-in-kind

PIK interest capitalizes into principal at each payment date.

## Senior tranches

Senior bonds accrue on an actual/360 basis.
"""


def test_markdown_chunks_carry_section_path():
    texts, metadatas = pipeline._split_markdown(MARKDOWN_FIXTURE, {"source": "test.md"})
    assert texts, "expected chunks from markdown fixture"
    sections = [m.get("section", "") for m in metadatas]
    assert any("Mezzanine tranches" in s for s in sections)
    assert any("Payment-in-kind" in s for s in sections)
    # base metadata preserved on every chunk
    assert all(m.get("source") == "test.md" for m in metadatas)


def test_markdown_oversized_section_is_split(monkeypatch):
    monkeypatch.setattr(pipeline, "RAG_CHUNK_SIZE", 200)
    monkeypatch.setattr(pipeline, "RAG_CHUNK_OVERLAP", 20)
    big_section = "# Big\n\n" + ("Accrual details sentence. " * 60)
    texts, metadatas = pipeline._split_markdown(big_section, {})
    assert len(texts) > 1
    assert all(len(t) <= 300 for t in texts)


# ---------------------------------------------------------------------------
# Loader routing and fallback
# ---------------------------------------------------------------------------


def test_markdown_file_loads_as_markdown(tmp_path):
    p = tmp_path / "note.md"
    p.write_text("# Heading\n\nBody")
    text, fmt = pipeline.load_document(str(p))
    assert fmt == "markdown"
    assert "Heading" in text


def test_text_file_loads_as_text(tmp_path):
    p = tmp_path / "note.txt"
    p.write_text("plain content")
    text, fmt = pipeline.load_document(str(p))
    assert fmt == "text"
    assert text == "plain content"


def test_pdf_falls_back_to_pypdf_without_docling(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "_docling_available", lambda: False)
    called = {}

    def fake_pdf(filepath):
        called["filepath"] = filepath
        return "pdf text"

    monkeypatch.setattr(pipeline, "_load_pdf", fake_pdf)
    p = tmp_path / "doc.pdf"
    p.write_bytes(b"%PDF-1.4 fake")
    text, fmt = pipeline.load_document(str(p))
    assert text == "pdf text"
    assert fmt == "text"
    assert called["filepath"] == str(p)


def test_pdf_uses_docling_when_available(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "_docling_available", lambda: True)
    monkeypatch.setattr(pipeline, "_load_with_docling", lambda fp: "# Parsed\n\n| a | b |")
    p = tmp_path / "doc.pdf"
    p.write_bytes(b"%PDF-1.4 fake")
    text, fmt = pipeline.load_document(str(p))
    assert fmt == "markdown"
    assert text.startswith("# Parsed")


# ---------------------------------------------------------------------------
# Contextual enrichment gating
# ---------------------------------------------------------------------------


def test_enrichment_disabled_is_noop():
    import asyncio

    service = pipeline.RAGPipelineService(MagicMock())
    assert pipeline.settings.rag_contextual_enrichment is False
    texts = ["chunk one", "chunk two"]
    out = asyncio.run(
        service._contextualize_chunks(MagicMock(), "full text", texts, [{}, {}])
    )
    assert out == texts


# ---------------------------------------------------------------------------
# Endpoint enforcement
# ---------------------------------------------------------------------------


@pytest.fixture
def rag_client(tmp_path):
    import uuid as _uuid
    from datetime import datetime

    mock_session = MagicMock()
    query = mock_session.query.return_value
    query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
    query.order_by.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []

    def fake_refresh(obj):
        # Simulate DB-side column defaults that only apply at flush time
        if getattr(obj, "id", None) is None:
            obj.id = _uuid.uuid4()
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.utcnow()
        if getattr(obj, "updated_at", None) is None:
            obj.updated_at = datetime.utcnow()
        if getattr(obj, "chunk_count", None) is None:
            obj.chunk_count = 0

    mock_session.refresh.side_effect = fake_refresh

    def override_get_sync_db():
        yield mock_session

    app = FastAPI()
    app.include_router(rag.router, prefix="/api/v1/rag")
    app.dependency_overrides[get_sync_db] = override_get_sync_db
    with TestClient(app) as client:
        yield client


def test_from_path_without_metadata_rejected(rag_client, tmp_path):
    assert get_settings().rag_enforce_metadata_contract is True
    p = tmp_path / "doc.md"
    p.write_text("# Doc")
    response = rag_client.post(
        "/api/v1/rag/documents/from-path", params={"filepath": str(p)}
    )
    assert response.status_code == 422
    assert "Metadata contract" in response.json()["detail"]


def test_from_path_with_invalid_metadata_rejected(rag_client, tmp_path):
    p = tmp_path / "doc.md"
    p.write_text("# Doc")
    bad = {**VALID_METADATA, "trust_level": "gospel"}
    response = rag_client.post(
        "/api/v1/rag/documents/from-path", params={"filepath": str(p)}, json=bad
    )
    assert response.status_code == 422
    assert "trust_level" in response.json()["detail"]


def test_from_path_with_valid_metadata_accepted(rag_client, tmp_path):
    p = tmp_path / "doc.md"
    p.write_text("# Doc")
    response = rag_client.post(
        "/api/v1/rag/documents/from-path", params={"filepath": str(p)}, json=VALID_METADATA
    )
    assert response.status_code == 200, response.text


def test_list_documents_with_corpus_filter(rag_client):
    response = rag_client.get("/api/v1/rag/documents", params={"domain": "custody"})
    assert response.status_code == 200
    assert response.json() == []
