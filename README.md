# Vellum-main / Otomeshon

A broad product prototype for banking operations automation, data workflows, knowledge graph tooling, and data sandbox exploration.

## First-pass repo truth

This repository currently contains both real platform code and demo/dev convenience paths. The purpose of this first-pass cleanup is to make those boundaries explicit.

### Source-of-truth decisions

- `Vellum-main` is the primary product repository.
- The canonical frontend architecture is **Next.js App Router**.
- The canonical backend API contract is **`/api/v1/...`**.
- The canonical full backend entrypoint is **`backend/app/main.py`**.
- The simplified backend entrypoint **`backend/app/main_simple.py`** is **demo/dev-only**.
- The separate `otomeshon-custodian-portal-main` repository should be treated as a **UI reference / donor**, not a replacement foundation.

## Repository shape

### Frontend
The repo currently contains:

- **Next.js App Router** files under `frontend/app/*`
- **legacy SPA-style files** under `frontend/src/main.tsx` and `frontend/src/App.tsx`

Going forward, the intended frontend runtime is the Next.js App Router path.

### Backend
The repo currently contains:

- **Full backend**: `backend/app/main.py`
- **Demo/dev backend**: `backend/app/main_simple.py`

The demo backend exists to support lightweight local work without requiring the full infrastructure stack.

## Run modes

See [`RUN_MODES.md`](RUN_MODES.md) for the intended mode split.

### Demo mode
- frontend: Next.js app in `frontend`
- backend: `backend/app/main_simple.py`
- purpose: fast local demos and lightweight development

### Development mode
- frontend: Next.js App Router
- backend: intended target is `backend/app/main.py`
- purpose: integration work against the real product architecture

### Full mode
- frontend + backend + infrastructure
- purpose: full-system validation

## Auth and API contract

The long-term target contract for the main application is:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/refresh`

The simplified backend may continue to expose `/api/auth/...` routes for demo/dev convenience, but that is not the intended long-term primary contract.

See [`AUTH_STRATEGY.md`](AUTH_STRATEGY.md) for details.

## Development

See [`DEVELOPMENT.md`](DEVELOPMENT.md) for practical local development instructions.

## Notes on current maturity

This repo has meaningful product breadth, but it is still in a consolidation phase. Some areas are real, some are partially integrated, and some remain demo-oriented. The immediate focus is architecture clarity, frontend/backend contract alignment, and reducing ambiguity in the codebase.
