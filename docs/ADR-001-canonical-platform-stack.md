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
| **Frontend** | **Product UI:** [`otomeshon-portal`](https://github.com/SPDough/otomeshon-portal) — Vite + React 18 + React Router + MUI. In-repo `Vellum/frontend` (Next.js) is non-canonical reference only. |
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
| `PREFECT_API_KEY` | Prefect Cloud API key (unset for local server profile) |
| `PREFECT_WORK_POOL` | Prefect work pool name for worker processes (e.g. `default-agent-pool`) |
| `STARTUP_ENABLE_TEMPORAL` | Default **`false`** in dev Compose; Temporal retained only during migration |

## Consequences

- **Temporal**: phased deprecation; new deterministic pipelines should be Prefect flows.
- **`Vellum/frontend` (Next.js)**: non-canonical reference only; product UI is **otomeshon-portal**.
- **Two frontends temporarily**: allowed during cleanup, but both must target this stack document for API conventions (`/api/v1/...`).

## References

- `RUN_MODES.md` — run modes vs canonical backend
- `backend/flows/canonical_probe.py` — minimal Prefect flow smoke artifact
- `docs/PREFECT-CLOUD-WORK-POOLS.md` — Cloud work pool runbook and local/CI wiring
