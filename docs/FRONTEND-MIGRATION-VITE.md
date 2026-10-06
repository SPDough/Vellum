# `Vellum/frontend` Vite migration — complete

Canonical UI stack is **Vite + React 18 + React Router + MUI v7** (same as `otomeshon-portal`). `Vellum/frontend` has been fully migrated off Next.js onto this stack:

- Single bundler: **Vite** (`vite.config.ts`, `index.html`)
- Routing: **React Router v6** (`HashRouter`), one central route table in `src/App.tsx`
- API client: `axios` wrapper in `src/services/api.ts`, `VITE_API_URL` env var, base path includes `/api/v1`
- Auth: real route protection via `ProtectedRoute` gating on `useAuthStore`
- Styling: **MUI v7** only (Grid v2 API migrated via `@mui/codemod v7.0.0/grid-props`)
- All Next.js artifacts removed: `next.config.js`, `app/`, the `next` dependency, and the dead `NextLayout`/`AuthContext`/`AuthGuard` cluster that never wired into the live app.

See `ARCHITECTURE.md`'s "Frontend truth" section for the current state.
