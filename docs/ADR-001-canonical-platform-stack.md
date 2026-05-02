# ADR-001: Canonical platform stack

## Status

Accepted — execution started 2026-05-01.

## Context

Otomeshon spans multiple repositories (`Vellum` backend + UIs, `otomeshon-portal`). We need a single documented stack so engineering, DevOps, and AI behavior stay aligned.

## Decision

| Layer | Choice |
|-------|--------|
| **Data** | PostgreSQL + **pgvector** for embeddings and RAG-backed features |
| **API** | **FastAPI** (`app.main`), contract under `/api/v1/...` |
| **Deterministic orchestration** | **Prefect** (local server in Compose; **Prefect Cloud** free tier for deployed agents) replaces Temporal as the default orchestration path over time |
| **Agentic workflows** | **LangGraph** for branching / tool-using automation (not for simple cron DAGs) |
| **Reasoning LLM** | **Anthropic Claude** as primary chat/reasoning provider when `ANTHROPIC_API_KEY` is set |
| **Embeddings** | **OpenAI `text-embedding-3-small`** as primary embedding model when `OPENAI_API_KEY` is set (pgvector dimensions must match 1536 for this model) |
| **Frontend** | **Vite + React 18 + React Router + MUI v7**; **no Tailwind** in product UIs; Radix primitives allowed only where MUI does not cover a11y needs (revisit periodically) |
| **Local dev** | **Docker Compose** (`docker-compose.dev.yml`) for integrated services |
| **Scheduled / cloud orchestration** | **Prefect Cloud** (free tier) for managed work pools; API URL via `PREFECT_API_URL` |

## Configuration (environment)

| Variable | Purpose |
|----------|---------|
| `LLM_PRIMARY_PROVIDER` | `anthropic` (default), `openai`, or `ollama` |
| `ANTHROPIC_DEFAULT_MODEL` | Default Claude model id (e.g. `claude-3-5-sonnet-20241022`) |
| `OPENAI_EMBEDDING_MODEL` | Default `text-embedding-3-small` |
| `EMBEDDING_PRIMARY_PROVIDER` | `openai` (default when key present), `ollama`, or `sentence_transformer` |
| `PREFECT_API_URL` | e.g. `http://prefect-server:4200/api` (Compose) or Prefect Cloud API URL |
| `STARTUP_ENABLE_TEMPORAL` | Default **`false`** in dev Compose; Temporal retained only during migration |

## Consequences

- **Temporal**: phased deprecation; new deterministic pipelines should be Prefect flows.
- **`Vellum/frontend` (Next.js)**: non-canonical; migrate toward Vite + RR + MUI to match `otomeshon-portal` (see `docs/FRONTEND-MIGRATION-VITE.md`).
- **Two frontends**: allowed, but both must target this stack document for framework and API conventions.

## References

- `RUN_MODES.md` — run modes vs canonical backend
- `backend/flows/canonical_probe.py` — minimal Prefect flow smoke artifact
