"""
Ownership/listing/TTL index for knowledge-agent conversations.

The turn-by-turn state lives in the LangGraph Postgres checkpointer; this service
manages the `knowledge_conversations` metadata rows: create/touch on each turn,
owner-scoped get/list, and delete. All reads are filtered by `owner` (user_id) —
the isolation boundary.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.rag import KnowledgeConversation

settings = get_settings()


class KnowledgeConversationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _expiry(self, base: Optional[datetime] = None) -> datetime:
        return (base or datetime.utcnow()) + timedelta(days=settings.rag_conversation_ttl_days)

    def get_for_owner(
        self, conversation_id: uuid.UUID, owner: str
    ) -> Optional[KnowledgeConversation]:
        """Fetch a conversation only if it belongs to `owner` (else None)."""
        conv = self.db.get(KnowledgeConversation, conversation_id)
        if conv is None or conv.owner != owner:
            return None
        return conv

    def exists(self, conversation_id: uuid.UUID) -> Optional[KnowledgeConversation]:
        return self.db.get(KnowledgeConversation, conversation_id)

    def list_for_owner(
        self, owner: str, *, limit: int = 50, offset: int = 0
    ) -> List[KnowledgeConversation]:
        return (
            self.db.query(KnowledgeConversation)
            .filter(KnowledgeConversation.owner == owner)
            .order_by(KnowledgeConversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def touch(
        self,
        conversation_id: uuid.UUID,
        owner: str,
        *,
        title: str,
        added_messages: int = 2,
    ) -> KnowledgeConversation:
        """Create the conversation row (first turn) or refresh it (later turns).

        Refreshes `updated_at`/`expires_at` and bumps `message_count`. Title is
        only set on creation.
        """
        now = datetime.utcnow()
        conv = self.db.get(KnowledgeConversation, conversation_id)
        if conv is None:
            conv = KnowledgeConversation(
                id=conversation_id,
                owner=owner,
                title=(title or "New conversation")[:512],
                created_at=now,
                updated_at=now,
                expires_at=self._expiry(now),
                message_count=added_messages,
            )
            self.db.add(conv)
        else:
            conv.updated_at = now
            conv.expires_at = self._expiry(now)
            conv.message_count = (conv.message_count or 0) + added_messages
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def delete_for_owner(self, conversation_id: uuid.UUID, owner: str) -> bool:
        """Delete the conversation row if owned by `owner`. Returns True if deleted.

        Checkpoint rows are deleted separately by the caller (async saver).
        """
        conv = self.get_for_owner(conversation_id, owner)
        if conv is None:
            return False
        self.db.delete(conv)
        self.db.commit()
        return True

    def expired_ids(self, *, now: Optional[datetime] = None, limit: int = 1000) -> List[uuid.UUID]:
        """Ids of conversations past their TTL (for the cleanup flow)."""
        cutoff = now or datetime.utcnow()
        rows = (
            self.db.query(KnowledgeConversation.id)
            .filter(KnowledgeConversation.expires_at.isnot(None))
            .filter(KnowledgeConversation.expires_at < cutoff)
            .limit(limit)
            .all()
        )
        return [r[0] for r in rows]
