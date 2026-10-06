# Architecture

This document is the first-pass truth source for `Vellum-main`.

## Current source-of-truth decisions

- `Vellum-main` is the primary product repository.
- The frontend target architecture is **Vite + React 18 + React Router + MUI v7** (migrated off Next.js).
- The backend primary API contract is **`/api/v1/...`**.
- The real backend entrypoint is **`backend/app/main.py`**.
- The simplified backend entrypoint **`backend/app/main_simple.py`** is **demo/dev-only**.
- The sibling [`otomeshon-portal`](https://github.com/SPDough/otomeshon-portal) repository targets the same stack (Vite + React Router + MUI) and the same `/api/v1/...` backend contract.

## Frontend truth

`frontend/` is a Vite + React Router + MUI v7 SPA (`HashRouter`). Next.js has
been fully removed — no `next.config.js`, no `app/` directory, no `next`
dependency. Routes live in `frontend/src/App.tsx`; page components live under
`frontend/src/components/pages/*`.

## Backend truth

There are two backend modes in the repository:

### Real backend
- Entry: `backend/app/main.py`
- Purpose: full platform backend
- Contract: ` /api/v1/... `
- Characteristics: real service wiring, database initialization, knowledge graph, background systems

### Demo/dev backend
- Entry: `backend/app/main_simple.py`
- Purpose: local demo / lightweight development without full infrastructure
- Contract: mixed demo routes, including `/api/auth/...` and `/api/v1/data-sandbox/...`
- Characteristics: sample data, simplified auth, no full infrastructure requirements

## Auth truth

The long-term frontend/backend contract should use:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/refresh`

The simplified backend currently exposes `/api/auth/...` routes for demo mode. That is a compatibility layer for demo/dev usage, not the target long-term contract.

## First-pass cleanup goals

This first pass is focused on:

- documenting the real architecture
- reducing confusion about which frontend path is active
- reducing confusion about which backend path is real
- aligning frontend auth/API usage toward the `/api/v1` contract
- clearly labeling migration leftovers and demo-only code

## Explicitly deferred to later passes

Not part of this first pass:

- deleting all legacy frontend files
- full frontend redesign
- complete auth redesign
- complete service consolidation
- full startup modularization
- full type/lint cleanup
