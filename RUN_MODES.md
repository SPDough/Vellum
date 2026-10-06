# Run Modes

This file defines the intended run modes for `Vellum-main`.

**Canonical stack (architecture):** see [`docs/ADR-001-canonical-platform-stack.md`](docs/ADR-001-canonical-platform-stack.md).


## 1. Demo mode

### Purpose
Use this mode for fast local demos and lightweight development when full infrastructure is not available.

### Frontend
- Target frontend: `frontend` Vite app on port `3000`

### Backend
- Entry: `backend/app/main_simple.py`
- Default port: `8000`

### Characteristics
- sample data only
- simplified auth
- no requirement for PostgreSQL / Neo4j / Kafka / Prefect
- useful for quick UI and API demos

### Important limitation
Demo mode is **not** the production architecture. It exists to reduce local setup friction.

## 2. Development mode

### Purpose
Use this mode for day-to-day engineering against the intended product architecture.

### Frontend
- Canonical runtime: Vite + React Router in `frontend/src/App.tsx`

### Backend
- Intended entry: `backend/app/main.py`

### Characteristics
- should align with the real `/api/v1/...` backend contract
- may still use reduced infrastructure depending on local setup
- should be the default target for integration work

## 3. Full mode

### Purpose
Use this mode for the full platform stack.

### Characteristics
- real backend
- full infrastructure enabled
- intended for full-system validation
- may require PostgreSQL, Neo4j, Kafka, Prefect, and other supporting services

## Frontend architecture note

The frontend is a Vite + React Router SPA. Next.js has been fully removed.

## API contract note

The long-term API contract for the main application is:

- `/api/v1/...`

Any `/api/auth/...` paths currently present in the simplified backend should be treated as demo/dev compatibility behavior, not the final primary contract.

## CI and integration targets

- **Canonical backend for PRs and Portal wiring:** `uvicorn app.main:app` (module `backend/app/main.py`). OpenAPI and contract tests should target this app only.
- **Demo / no-infra smoke:** `app.main_simple:app` is allowed for quick UI checks; it is **not** a substitute for `app.main` in integration tests.
- **Environment flags for CI without Neo4j/Kafka:** Postgres-first defaults keep `STARTUP_ENABLE_NEO4J`, `STARTUP_ENABLE_KAFKA`, and `STARTUP_ENABLE_KG_SYNC` false. `ENVIRONMENT=testing` also defaults these flags to false; override them only when those services are available.
- **Auth:** `JwtAuthMiddleware` validates HS256 Bearer tokens. Set `AUTH_REQUIRED=true` (or `ENVIRONMENT=production`) to reject anonymous API calls. Invalid tokens are always rejected.
