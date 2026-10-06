"""JWT auth middleware unit tests (P2 harden)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.core.config import get_settings
from app.core.jwt_auth import JwtAuthMiddleware, decode_access_token


def _make_token(**claims) -> str:
    settings = get_settings()
    payload = {
        "type": "access",
        "email": "ops@vellum.ops",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        **claims,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


@pytest.fixture
def app_with_auth(monkeypatch):
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()

    async def ping(request: Request):
        return JSONResponse(
            {"subject": getattr(request.state, "auth_subject", None)}
        )

    app = Starlette(routes=[Route("/api/v1/oversight/run", ping, methods=["GET"])])
    app.add_middleware(JwtAuthMiddleware)
    yield TestClient(app)
    get_settings.cache_clear()


def test_decode_access_token_accepts_valid():
    token = _make_token()
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["email"] == "ops@vellum.ops"


def test_decode_access_token_rejects_wrong_type():
    settings = get_settings()
    token = jwt.encode(
        {
            "type": "refresh",
            "email": "ops@vellum.ops",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        settings.secret_key,
        algorithm="HS256",
    )
    assert decode_access_token(token) is None


def test_middleware_rejects_missing_token_when_required(app_with_auth):
    response = app_with_auth.get("/api/v1/oversight/run")
    assert response.status_code == 401


def test_middleware_rejects_invalid_token(app_with_auth):
    response = app_with_auth.get(
        "/api/v1/oversight/run",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert response.status_code == 401


def test_middleware_accepts_valid_token(app_with_auth):
    token = _make_token()
    response = app_with_auth.get(
        "/api/v1/oversight/run",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["subject"] == "ops@vellum.ops"
