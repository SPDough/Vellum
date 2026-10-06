"""API-level oversight slice smoke (dependency overrides, no live Postgres)."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.endpoints import oversight as oversight_endpoint
from app.oversight.repository import InMemoryOversightRepository
from app.oversight.service import OversightService
from app.rules.engine import RuleEngine


@pytest.fixture
def oversight_client():
    app = FastAPI()
    app.include_router(oversight_endpoint.router, prefix="/api/v1")

    service = OversightService(
        repository=InMemoryOversightRepository(), engine=RuleEngine()
    )

    async def _override():
        return service

    app.dependency_overrides[oversight_endpoint.get_oversight_service] = _override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_oversight_run_and_explain_roundtrip(oversight_client):
    run = oversight_client.post("/api/v1/oversight/run")
    assert run.status_code == 200
    body = run.json()
    assert body["summary"]["breaks"] >= 1
    assert body["run_id"]

    runs = oversight_client.get("/api/v1/oversight/runs")
    assert runs.status_code == 200
    assert any(r["run_id"] == body["run_id"] for r in runs.json())

    break_id = body["breaks"][0]["payload"]["break_id"]
    explain = oversight_client.get(f"/api/v1/oversight/breaks/{break_id}/explain")
    assert explain.status_code == 200
    explained = explain.json()
    assert explained["break_id"] == break_id
    assert "expertise_levels" in explained
    assert explained["expertise_levels"]["operator"]


def test_sample_csv_ingest_endpoint(oversight_client):
    response = oversight_client.post("/api/v1/oversight/ingest/sample-csv")
    assert response.status_code == 200
    assert response.json()["summary"]["source"] == "csv_ingest"


def test_break_lifecycle_transitions_and_audit(oversight_client):
    run = oversight_client.post("/api/v1/oversight/run")
    assert run.status_code == 200
    break_id = run.json()["breaks"][0]["payload"]["break_id"]

    ack = oversight_client.patch(
        f"/api/v1/oversight/breaks/{break_id}/status",
        json={
            "status": "acknowledged",
            "assignee": "ops.desk",
            "actor": "test-user",
            "note": "Looking into qty mismatch",
        },
    )
    assert ack.status_code == 200
    body = ack.json()
    assert body["status"] == "acknowledged"
    assert body["assignee"] == "ops.desk"
    assert body["event"]["from_status"] == "open"

    resolve = oversight_client.patch(
        f"/api/v1/oversight/breaks/{break_id}/status",
        json={"status": "resolved", "actor": "test-user", "note": "Fixed upstream"},
    )
    assert resolve.status_code == 200
    assert resolve.json()["status"] == "resolved"

    illegal = oversight_client.patch(
        f"/api/v1/oversight/breaks/{break_id}/status",
        json={"status": "acknowledged", "actor": "test-user"},
    )
    assert illegal.status_code == 409

    events = oversight_client.get(f"/api/v1/oversight/breaks/{break_id}/events")
    assert events.status_code == 200
    trail = events.json()
    assert len(trail) == 2
    assert trail[0]["to_status"] == "acknowledged"
    assert trail[1]["to_status"] == "resolved"

    explain = oversight_client.get(f"/api/v1/oversight/breaks/{break_id}/explain")
    assert explain.status_code == 200
    assert explain.json()["status"] == "resolved"
    assert explain.json()["assignee"] == "ops.desk"
