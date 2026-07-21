# Design: Multi-turn memory for the knowledge agent

**Status:** Proposed — open questions resolved 2026-07-21; ready to implement on approval
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
    messages: Annotated[list[ChatTurn], add_messages]  # accumulates across turns (persisted; ChatTurn carries citations — see §5.3)
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
- **Threads are keyed on `user_id`** (the authenticated user). Every conversation carries an `owner = user_id`; the API rejects a `conversation_id` whose owner ≠ the caller (404, never another user's thread). Session id is not used as the isolation boundary — a user's conversations follow them across sessions/devices.

## 5. Persistence design

### 5.1 Checkpointer

- Dependency: `langgraph-checkpoint-postgres` (add to `backend/requirements.txt`).
- `AsyncPostgresSaver` (async API path) built from the existing `DATABASE_URL`; `graph.compile(checkpointer=saver)`.
- Tables (`checkpoints`, `checkpoint_writes`, `checkpoint_blobs`) are created via **Alembic migration `005`** (decided), not `saver.setup()` at startup — for auditability and parity with how we ship all other schema. The migration reproduces the checkpointer's DDL; we pin the `langgraph-checkpoint-postgres` version so the schema stays in sync, and add a startup assertion that the expected tables exist.

### 5.2 Conversation index table (for listing/UX)

The checkpointer stores state per thread but is **not** a good source for "list my conversations with titles." Add a thin table:

```
knowledge_conversations(
  id uuid pk,                    -- == thread_id
  owner text not null,           -- user_id; the isolation boundary
  title text,                    -- derived from the first question
  created_at, updated_at,
  expires_at timestamptz,        -- updated_at + TTL; drives retention cleanup
  message_count int
)
```

- Populated on first turn; `title` = first question (optionally LLM-summarized later).
- `owner = user_id` is the isolation boundary for all conversation endpoints.
- `expires_at` is recomputed on each turn (`updated_at + RAG_CONVERSATION_TTL_DAYS`) so active conversations stay alive and idle ones age out (§9).

### 5.3 Message + citation persistence

Per the decision to **persist citations**, each assistant turn stores its citations alongside the message. Message content is carried in the checkpointer's `messages` channel (the durable source of truth for a thread):

```python
class ChatTurn(TypedDict):
    role: Literal["user", "assistant"]
    content: str
    citations: list[Citation]   # [] for user turns; populated for assistant turns
    created_at: str
```

Because citations live inside the persisted `messages` channel, `GET /conversations/{id}` returns each assistant turn **with its original citations** — no recomputation, and the exact sources shown at answer time are preserved for audit.

## 6. History windowing

- Feed the **last `RAG_AGENT_MAX_HISTORY_TURNS`** messages (default 6 ≈ 3 exchanges) to both `contextualize` and `synthesize`.
- Bounds token cost/latency; predictable. Summarization of older turns is a later enhancement (§11).

## 7. API design

- `POST /api/v1/rag/knowledge/ask`
  - Request: `{ query, conversation_id?, filters?, min_trust? }`
  - Response: `{ conversation_id, answer, route, iterations, citations }` (id minted on first turn)
  - No `conversation_id` ⇒ single-shot, exactly as today (backward compatible).
- `GET /api/v1/rag/knowledge/conversations` — list caller's conversations (id, title, updated_at).
- `GET /api/v1/rag/knowledge/conversations/{id}` — full message history, each assistant turn **including its persisted citations** (owner-checked).
- `DELETE /api/v1/rag/knowledge/conversations/{id}` — delete conversation + its checkpoint state (owner-checked).

## 8. Configuration

| Env var | Default | Purpose |
|---|---|---|
| `RAG_AGENT_MEMORY_ENABLED` | `true` | Master switch; off ⇒ pure single-shot |
| `RAG_AGENT_MAX_HISTORY_TURNS` | `6` | Messages fed to contextualize/synthesis |
| `RAG_AGENT_CHECKPOINTER` | `postgres` | `postgres` \| `memory` (dev) |
| `RAG_CONVERSATION_TTL_DAYS` | `90` | Idle-conversation retention; drives `expires_at` + cleanup |
| (reuses `DATABASE_URL`) | — | Checkpointer connection |

## 9. Security & privacy

- **Isolation:** every conversation endpoint filters by `owner`; a mismatched `conversation_id` returns 404, never another user's thread.
- **Retention (TTL):** conversations expire after `RAG_CONVERSATION_TTL_DAYS` of inactivity (default 90). `expires_at` is refreshed on every turn. A scheduled **Prefect flow** (`knowledge_conversation_cleanup`, daily) deletes expired conversations and their checkpointer rows — using Prefect keeps this consistent with the rest of our scheduled orchestration (ADR-001).
- **Deletion:** both `DELETE /conversations/{id}` and the TTL cleanup must remove the `knowledge_conversations` row **and** all checkpointer rows (`checkpoints`, `checkpoint_writes`, `checkpoint_blobs`) for that `thread_id` — no orphaned state.
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

## 12. Resolved decisions

All four open questions are resolved (2026-07-21):

1. **Checkpointer DDL** → **Alembic migration `005`** (not `setup()` at startup). §5.1.
2. **Thread `owner`** → **`user_id`** (authenticated user; follows the user across sessions/devices). §4.4.
3. **Retention** → **TTL**, default `RAG_CONVERSATION_TTL_DAYS = 90` days of inactivity, enforced by a daily Prefect cleanup flow. §9.
4. **Citations in history** → **persist** per-turn citations inside the `messages` channel; history returns the exact sources shown at answer time (no recompute). §5.3, §7.

No open questions remain; the design is ready to implement on approval.

## 13. Phasing (post-approval)

1. **Backend memory core** — contextualize node, `messages` state + reset, `thread_id` plumbing, `MemorySaver` first (proves multi-turn works).
2. **Durable persistence** — Postgres checkpointer + `knowledge_conversations` + history endpoints (migration 005).
3. **Frontend (portal)** — `KnowledgeAssistant` carries `conversation_id`; optional history list/new-conversation (reuse the ChatDrawer pattern).
4. **Eval** — multi-turn golden cases in the Phase 3 harness.

## 14. Touch points (estimate)

- `knowledge_agent.py` (contextualize node, state, reset, checkpointer wiring)
- `knowledge_tool.py`, `api/endpoints/rag.py`, `schemas/rag.py` (thread id + conversation endpoints)
- `models/rag.py` + migration `005` (checkpoint tables + `knowledge_conversations` with `owner`/`expires_at`)
- `backend/flows/knowledge_conversation_cleanup.py` (daily TTL cleanup Prefect flow)
- `core/config.py` (new env vars)
- `tests/` (unit + multi-turn eval)
- Portal `KnowledgeAssistant.tsx` + `knowledgeApi.ts` (conversation id)
