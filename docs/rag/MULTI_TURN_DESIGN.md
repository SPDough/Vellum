# Design: Multi-turn memory for the knowledge agent

**Status:** Proposed (design review) — 2026-07-21
**Scope:** `backend/app/ai/langgraph_workflows/knowledge_agent.py` and its API/tool surface
**Related:** [ADR-001 canonical stack](../ADR-001-canonical-platform-stack.md), [RAG_MVP_ARCHITECTURE](RAG_MVP_ARCHITECTURE.md)

## 1. Context

The knowledge agent (`knowledge_lookup`) is currently **single-shot**: every `run()` starts from a fresh state, retrieves, and answers one contextless question. There is no checkpointer, no conversation history, no `thread_id`.

Users increasingly ask **follow-ups** — *"What is a mezzanine bond?"* → *"How does **it** accrue interest?"* → *"And the tax treatment?"*. Two things break without memory:

1. **Retrieval breaks.** *"How is that taxed?"* is a poor standalone retrieval query — the pronoun carries the topic. Dense + sparse retrieval both need a self-contained question.
2. **Answers lose coherence.** Synthesis has no idea what "that" refers to.

This document specifies how we add durable multi-turn memory while keeping single-shot behavior intact.

## 2. Goals / non-goals

**Goals**
- Follow-up questions resolve correctly (pronouns/ellipsis → standalone query for retrieval).
- Conversation state is **durable** (survives restarts) and **auditable**.
- Backward compatible: a request with no conversation id behaves exactly as today.
- Thread state is isolated per user/session (no cross-user leakage).

**Non-goals (this iteration)**
- Cross-conversation long-term user memory / personalization.
- Summarization-based history compression (deferred; see §11 Alternatives).
- Changing the retrieval/rerank stack (Phase 2) or the grade/rewrite loop (Phase 3).

## 3. Decisions (agreed)

| Decision | Choice | Rationale |
|---|---|---|
| Persistence backend | **Postgres checkpointer** (`langgraph-checkpoint-postgres`) | Durable + auditable; reuses the Postgres we already run; idiomatic LangGraph. Matches ADR-001 (Postgres canonical, LangGraph for agentic flows). |
| History windowing | **Last N turns** (`RAG_AGENT_MAX_HISTORY_TURNS`, default 6 messages) | Predictable cost/latency; simplest correct behavior. |
| Delivery | **Design-first**, then phased implementation | This document is the review gate before code. |

## 4. Architecture

### 4.1 New node: `contextualize` (condense-question)

A new entry node turns `(recent history + new question)` into a **standalone question** before classification/retrieval.

- Input: last N messages + the new user turn.
- Output: `original_query` = a self-contained question.
- If the turn is already standalone (first turn, or a clear topic switch), it passes through unchanged.
- `temperature=0`; graceful degradation: if no LLM, use the raw question (single-shot behavior).

This is the single most important addition — it is what makes retrieval work across turns.

### 4.2 Graph shape

```
[restore thread state] → contextualize → classify → retrieve ─┬─(simple)──────────► synthesize → END
                          (standalone Q)                       └─(complex)─► grade ─┬─(ok|cap)─► synthesize → END
                                                                                    └─► rewrite ─┐
                                                                                       ▲          │
                                                                                       └ retrieve ┘
```

Everything from `classify` onward is unchanged from Phase 3.

### 4.3 State changes

```python
class KnowledgeAgentState(TypedDict, total=False):
    messages: Annotated[list[ChatTurn], add_messages]  # accumulates across turns (persisted)
    # per-turn working fields — RESET at the start of every turn:
    query: str
    original_query: str
    route: str
    candidates: list[RetrievalCandidate]
    iterations: int
    sufficient: bool
    grade_reason: str
    answer: str
    trace: list[dict]
```

- Only `messages` accumulates (append reducer). The checkpointer restores it each turn.
- **Critical:** the entry node must **reset the per-turn working fields** to defaults every turn. Because the checkpointer restores the *entire* prior state, stale `candidates`/`iterations` from the previous question would otherwise leak into this one. (This is the classic multi-turn-with-checkpointer bug; call it out in tests.)
- `candidates` are heavy (chunk text) and must **not** be persisted long-term — either keep them out of the persisted channels or clear them before the turn ends. Persist only `messages` (+ optionally the last turn's citations for display).

### 4.4 Thread identity

- `thread_id == conversation_id`, passed via `config={"configurable": {"thread_id": conversation_id}}`.
- Conversation ids are **scoped to the authenticated user/session**; the API must reject a `conversation_id` that doesn't belong to the caller (no cross-user thread access).

## 5. Persistence design

### 5.1 Checkpointer

- Dependency: `langgraph-checkpoint-postgres` (add to `backend/requirements.txt`).
- `AsyncPostgresSaver` (async API path) built from the existing `DATABASE_URL`; `graph.compile(checkpointer=saver)`.
- Tables (`checkpoints`, `checkpoint_writes`, `checkpoint_blobs`) are created by the saver's `setup()`. **Decision needed:** run `setup()` on startup vs. wrap the DDL in an Alembic migration (§12 open question). Recommendation: Alembic migration `005` for auditability and parity with how we ship schema.

### 5.2 Conversation index table (for listing/UX)

The checkpointer stores state per thread but is **not** a good source for "list my conversations with titles." Add a thin table:

```
knowledge_conversations(
  id uuid pk,
  owner text not null,          -- user/session id; enforces isolation
  title text,                    -- derived from the first question
  created_at, updated_at,
  message_count int
)
```

- Populated on first turn; `title` = first question (optionally LLM-summarized later).
- `owner` is the isolation boundary for all conversation endpoints.

## 6. History windowing

- Feed the **last `RAG_AGENT_MAX_HISTORY_TURNS`** messages (default 6 ≈ 3 exchanges) to both `contextualize` and `synthesize`.
- Bounds token cost/latency; predictable. Summarization of older turns is a later enhancement (§11).

## 7. API design

- `POST /api/v1/rag/knowledge/ask`
  - Request: `{ query, conversation_id?, filters?, min_trust? }`
  - Response: `{ conversation_id, answer, route, iterations, citations }` (id minted on first turn)
  - No `conversation_id` ⇒ single-shot, exactly as today (backward compatible).
- `GET /api/v1/rag/knowledge/conversations` — list caller's conversations (id, title, updated_at).
- `GET /api/v1/rag/knowledge/conversations/{id}` — full message history (owner-checked).
- `DELETE /api/v1/rag/knowledge/conversations/{id}` — delete conversation + its checkpoint state (owner-checked).

## 8. Configuration

| Env var | Default | Purpose |
|---|---|---|
| `RAG_AGENT_MEMORY_ENABLED` | `true` | Master switch; off ⇒ pure single-shot |
| `RAG_AGENT_MAX_HISTORY_TURNS` | `6` | Messages fed to contextualize/synthesis |
| `RAG_AGENT_CHECKPOINTER` | `postgres` | `postgres` \| `memory` (dev) |
| (reuses `DATABASE_URL`) | — | Checkpointer connection |

## 9. Security & privacy

- **Isolation:** every conversation endpoint filters by `owner`; a mismatched `conversation_id` returns 404, never another user's thread.
- **Retention/deletion:** `DELETE` must remove both the `knowledge_conversations` row and the checkpointer rows for that `thread_id`.
- **Stored content:** conversation messages may contain sensitive queries; storage inherits the DB's protections; document retention policy with the data owner.
- **Audit:** durable threads + existing per-run trace logging give a reviewable history of what was asked and what was cited.

## 10. Testing & eval

- **Unit:** contextualize resolves a pronoun follow-up to a standalone query; per-turn working-state reset (no candidate leakage); owner-scoped access control; single-shot path unchanged when memory disabled.
- **Multi-turn eval:** golden 2–3 turn threads where turn *n* depends on turn *n−1*, scored for follow-up resolution + groundedness (extends the Phase 3 harness).

## 11. Alternatives considered

- **Client-passed history** (stateless server): simpler, but not durable or auditable, and duplicates history on every request. Rejected for a banking product.
- **`MemorySaver` only:** in-process, lost on restart. Kept as the `memory` dev option, not the default.
- **Summarization windowing:** better for very long chats; deferred — last-N is sufficient and simpler now.
- **Full ReAct agent:** rejected in Phase 3 for predictability; unchanged here.

## 12. Open questions for reviewers

1. **Checkpointer DDL:** Alembic migration `005` (recommended) vs. saver `setup()` at startup?
2. **`owner` source:** which identity do we key threads on — authenticated user id, session id, or both? (Depends on the portal/Vellum auth model in play.)
3. **Retention policy:** default TTL for conversations, or keep until explicit delete?
4. **Citations in history:** persist per-turn citations for re-render, or recompute on history fetch?

## 13. Phasing (post-approval)

1. **Backend memory core** — contextualize node, `messages` state + reset, `thread_id` plumbing, `MemorySaver` first (proves multi-turn works).
2. **Durable persistence** — Postgres checkpointer + `knowledge_conversations` + history endpoints (migration 005).
3. **Frontend (portal)** — `KnowledgeAssistant` carries `conversation_id`; optional history list/new-conversation (reuse the ChatDrawer pattern).
4. **Eval** — multi-turn golden cases in the Phase 3 harness.

## 14. Touch points (estimate)

- `knowledge_agent.py` (contextualize node, state, reset, checkpointer wiring)
- `knowledge_tool.py`, `api/endpoints/rag.py`, `schemas/rag.py` (thread id + conversation endpoints)
- `models/rag.py` + migration `005` (conversations table + checkpoint tables)
- `core/config.py` (new env vars)
- `tests/` (unit + multi-turn eval)
- Portal `KnowledgeAssistant.tsx` + `knowledgeApi.ts` (conversation id)
