"""Unit tests for conversation owner resolution and TTL logic (no DB)."""

import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.api.endpoints.rag import get_conversation_owner
from app.services.knowledge_conversation_service import KnowledgeConversationService


def run(coro):
    return asyncio.run(coro)


# --- owner resolution -------------------------------------------------------


def test_owner_falls_back_to_header_then_anonymous():
    assert run(get_conversation_owner(credentials=None, x_user_id="user-42")) == "user-42"
    assert run(get_conversation_owner(credentials=None, x_user_id=None)) == "anonymous"


def test_owner_prefers_valid_token(monkeypatch):
    async def fake_validate(token):
        return SimpleNamespace(id="kc-user-7")

    import app.core.auth as auth

    monkeypatch.setattr(auth.keycloak_auth, "validate_token", fake_validate)
    creds = SimpleNamespace(credentials="a.jwt.token")
    # header present too, but the valid token wins
    assert run(get_conversation_owner(credentials=creds, x_user_id="header-user")) == "kc-user-7"


def test_owner_ignores_invalid_token(monkeypatch):
    async def fake_validate(token):
        raise ValueError("bad token")

    import app.core.auth as auth

    monkeypatch.setattr(auth.keycloak_auth, "validate_token", fake_validate)
    creds = SimpleNamespace(credentials="bad")
    assert run(get_conversation_owner(credentials=creds, x_user_id="header-user")) == "header-user"


# --- TTL expiry -------------------------------------------------------------


def test_expiry_is_now_plus_ttl(monkeypatch):
    from app.services import knowledge_conversation_service as mod

    monkeypatch.setattr(mod.settings, "rag_conversation_ttl_days", 30)
    svc = KnowledgeConversationService(MagicMock())
    base = datetime(2026, 1, 1)
    assert svc._expiry(base) == base + timedelta(days=30)
