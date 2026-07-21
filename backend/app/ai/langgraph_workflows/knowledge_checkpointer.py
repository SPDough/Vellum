"""
Checkpointer selection for the knowledge agent's conversation memory.

- `memory`  → in-process MemorySaver (Phase 1; lost on restart, single-process).
- `postgres`→ durable AsyncPostgresSaver over a shared psycopg connection pool
  (Phase 2). Tables are created by Alembic migration 005, so we never call
  `setup()` here.

The Postgres saver is async to construct (opens a pool), so it is fetched via
`await get_conversation_checkpointer()` from async call sites (the tool/endpoints)
and injected into `KnowledgeAgent`. The in-process memory saver is also exposed
synchronously for direct (test/degraded) construction.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_memory_saver: Any = None
_pg_pool: Any = None
_pg_saver: Any = None


def get_memory_saver():
    """Shared in-process MemorySaver singleton."""
    global _memory_saver
    if _memory_saver is None:
        from langgraph.checkpoint.memory import MemorySaver

        _memory_saver = MemorySaver()
    return _memory_saver


def default_sync_checkpointer():
    """Synchronous default for direct construction: memory saver or None.

    The Postgres saver requires async setup, so it is never returned here; async
    call sites use `get_conversation_checkpointer()` and inject it.
    """
    if not settings.rag_agent_memory_enabled:
        return None
    return get_memory_saver()


async def _get_pg_saver():
    global _pg_pool, _pg_saver
    if _pg_saver is None:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg.rows import dict_row
        from psycopg_pool import AsyncConnectionPool

        # Raw psycopg DSN (no SQLAlchemy "+psycopg" suffix). langgraph requires
        # autocommit + dict rows on the connection.
        _pg_pool = AsyncConnectionPool(
            conninfo=settings.database_url,
            open=False,
            max_size=settings.rag_agent_pg_pool_size,
            kwargs={"autocommit": True, "row_factory": dict_row, "prepare_threshold": 0},
        )
        await _pg_pool.open()
        _pg_saver = AsyncPostgresSaver(_pg_pool)
        logger.info("Knowledge agent Postgres checkpointer initialized")
    return _pg_saver


async def get_conversation_checkpointer():
    """Return the configured checkpointer (or None if memory is disabled)."""
    if not settings.rag_agent_memory_enabled:
        return None
    if settings.rag_agent_checkpointer == "postgres":
        try:
            return await _get_pg_saver()
        except Exception as e:  # pragma: no cover - infra dependent
            logger.warning("Postgres checkpointer unavailable (%s); using in-process memory", e)
            return get_memory_saver()
    return get_memory_saver()


async def delete_thread(checkpointer: Any, thread_id: str) -> None:
    """Delete all checkpoint rows for a thread, if the checkpointer supports it."""
    deleter = getattr(checkpointer, "adelete_thread", None)
    if deleter is None:
        return
    await deleter(thread_id)


async def get_thread_messages(checkpointer: Any, thread_id: str) -> Optional[list]:
    """Return the persisted `messages` for a thread's latest checkpoint, or None."""
    getter = getattr(checkpointer, "aget_tuple", None)
    if getter is None:
        return None
    tup = await getter({"configurable": {"thread_id": thread_id}})
    if tup is None:
        return None
    return tup.checkpoint.get("channel_values", {}).get("messages")
