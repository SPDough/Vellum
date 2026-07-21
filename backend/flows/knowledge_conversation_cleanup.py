"""
Prefect flow: TTL cleanup of expired knowledge-agent conversations.

Deletes conversations whose `expires_at` has passed, and their LangGraph
checkpointer state. Intended to run daily (deploy as a scheduled Prefect
deployment). Run locally (from backend/):

    python -m flows.knowledge_conversation_cleanup
"""

import asyncio
from typing import List

from prefect import flow, get_run_logger, task


@task(name="find-expired-conversations")
def find_expired(limit: int = 1000) -> List[str]:
    """Return ids of conversations past their TTL."""
    from app.core.database import SessionLocal
    from app.services.knowledge_conversation_service import KnowledgeConversationService

    with SessionLocal() as db:
        return [str(cid) for cid in KnowledgeConversationService(db).expired_ids(limit=limit)]


@task(name="delete-conversation-rows")
def delete_rows(conversation_ids: List[str]) -> int:
    """Delete the conversation index rows. Returns count deleted."""
    import uuid

    from app.core.database import SessionLocal
    from app.models.rag import KnowledgeConversation

    if not conversation_ids:
        return 0
    with SessionLocal() as db:
        deleted = 0
        for cid in conversation_ids:
            conv = db.get(KnowledgeConversation, uuid.UUID(cid))
            if conv is not None:
                db.delete(conv)
                deleted += 1
        db.commit()
        return deleted


@task(name="delete-checkpoint-state", retries=1)
def delete_checkpoints(conversation_ids: List[str]) -> int:
    """Delete checkpointer state for each expired thread. Returns count."""
    from app.ai.langgraph_workflows.knowledge_checkpointer import (
        delete_thread,
        get_conversation_checkpointer,
    )

    async def _run() -> int:
        checkpointer = await get_conversation_checkpointer()
        if checkpointer is None:
            return 0
        count = 0
        for cid in conversation_ids:
            try:
                await delete_thread(checkpointer, cid)
                count += 1
            except Exception:  # pragma: no cover - infra dependent
                pass
        return count

    return asyncio.run(_run())


@flow(name="knowledge-conversation-cleanup")
def knowledge_conversation_cleanup(limit: int = 1000) -> dict:
    """Delete expired conversations and their checkpoint state."""
    logger = get_run_logger()
    expired = find_expired(limit)
    if not expired:
        logger.info("No expired conversations to clean up")
        return {"expired": 0, "rows_deleted": 0, "checkpoints_deleted": 0}
    rows = delete_rows(expired)
    checkpoints = delete_checkpoints(expired)
    logger.info(
        "Cleaned up %s conversations (rows=%s, checkpoints=%s)", len(expired), rows, checkpoints
    )
    return {"expired": len(expired), "rows_deleted": rows, "checkpoints_deleted": checkpoints}


if __name__ == "__main__":
    print(knowledge_conversation_cleanup())
