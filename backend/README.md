# Backend

This backend currently supports two different runtime modes:

## 1. Full backend (canonical product backend)
- Entry: `app/main.py`
- Intended contract: `/api/v1/...`
- Purpose: real platform backend
- Characteristics: fuller service graph, database and infrastructure integrations, broader product scope

## 2. Simplified backend (demo/dev-only)
- Entry: `app/main_simple.py`
- Purpose: local demo and lightweight development
- Characteristics: sample data, simplified auth, reduced infrastructure requirements
- Important: this is **not** the canonical long-term production backend

## Contract clarification

The long-term intended backend contract for the main product is:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/refresh`

The simplified backend currently exposes demo-oriented auth routes under `/api/auth/...` for convenience.
That compatibility path should be treated as **demo/dev-only behavior**, not the primary long-term product contract.

## Testing reality

Most current backend tests are written against `app/main_simple.py`.
That means the existing suite primarily validates the simplified demo backend, not the full backend in `app/main.py`.

This is useful for fast local confidence, but it should not be misread as complete coverage of the real production-oriented backend.

## Recommended testing split

Going forward, tests should be categorized into:

- **demo-backend tests** — explicitly target `app/main_simple.py`
- **real-backend tests** — target `app/main.py`
- **integration tests with infrastructure** — require database and supporting services

## Development reminder

If you are updating frontend/backend contracts, prefer aligning to `/api/v1/...` and treat any `/api/auth/...` behavior as part of demo compatibility unless intentionally working in simplified mode.
