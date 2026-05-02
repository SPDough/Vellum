# Migrating `Vellum/frontend` to the canonical Vite stack

Canonical UI stack is **Vite + React 18 + React Router + MUI v7** (same as `otomeshon-portal`). The `Vellum/frontend` package today mixes **Next.js App Router** (`app/`) and a legacy **`src/`** SPA.

## Target end state

- Single bundler: **Vite**
- Routing: **React Router v6** (mirror patterns in `otomeshon-portal/src/App.tsx`)
- API client: axios or fetch wrapper with `VITE_*` env vars, base URL including `/api/v1`
- Auth: `/api/v1/auth/*` only (no hardcoded `/api/auth/*`)
- Styling: **MUI v7** only; remove Tailwind if introduced during migration

## Suggested migration order

1. **Scaffold** a Vite app beside the current tree (e.g. rename current `frontend` → `frontend-next-legacy`, create new `frontend` from `otomeshon-portal`’s `vite.config.ts` + `tsconfig` as a template).
2. **Port providers**: React Query `QueryClientProvider`, MUI `ThemeProvider`, error boundaries.
3. **Port feature modules** from `src/services/*` into `src/services/` with unchanged API paths relative to `/api/v1`.
4. **Port pages** from `app/*/page.tsx` and `src/components/pages/*` into RR routes one vertical at a time (data sandbox first, then workflows, etc.).
5. **Delete** Next-specific files (`next.config`, `app/` layout) when parity is reached.
6. **Update** root `docker-compose.dev.yml` `frontend` service build context and env (`VITE_*`).

Until migration completes, **new product UI** should ship in **`otomeshon-portal`**; treat `Vellum/frontend` as maintenance / extraction only unless blocked.
