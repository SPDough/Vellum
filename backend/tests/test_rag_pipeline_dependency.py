"""
Verify RAG pipeline FastAPI dependencies: get_sync_db -> get_rag_pipeline_service.

Regression: get_rag_pipeline_service must declare db: Session = Depends(get_sync_db)
or FastAPI cannot inject the session.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.endpoints import rag
from app.core.database import get_sync_db


@pytest.fixture
def rag_client() -> TestClient:
    mock_session = MagicMock()
    mock_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

    def override_get_sync_db():
        yield mock_session

    app = FastAPI()
    app.include_router(rag.router, prefix="/api/v1/rag")
    app.dependency_overrides[get_sync_db] = override_get_sync_db

    with TestClient(app) as client:
        yield client


def test_list_documents_resolves_rag_pipeline_dependency(rag_client: TestClient) -> None:
    """GET /documents uses Depends(get_rag_pipeline_service), which must receive Session from get_sync_db."""
    response = rag_client.get("/api/v1/rag/documents")
    assert response.status_code == 200
    assert response.json() == []
