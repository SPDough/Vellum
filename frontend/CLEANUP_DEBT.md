# Frontend Cleanup Debt

This file tracks the highest-value frontend cleanup items remaining after the
initial Vellum consolidation pass.

## 1. Duplicate lockfiles

Current state before cleanup:
- root lockfile: `../package-lock.json`
- frontend lockfile: `./package-lock.json`

Observed during this cleanup pass:
- active frontend dependency work was performed in `frontend/`
- the frontend lockfile reflects the current local install state better than the stale root lockfile

### Decision
Treat `frontend/package-lock.json` as the authoritative frontend lockfile for now.

### Next action
Remove or archive the stale root `package-lock.json` once repo-level package manager expectations are confirmed.

## 2. Build-check suppressions still enabled

`next.config.js` currently suppresses:
- ESLint failures during build
- TypeScript build failures during build

### Current reality
- standalone typecheck passes via `npm run type-check`
- build passes via `npm run build`

### Recommendation
Re-enable in stages:
1. restore lint clarity
2. stop ignoring ESLint during build
3. stop ignoring TypeScript build errors during build

## 3. Legacy SPA files retired from active source tree

These files were moved out of `frontend/src/` into `frontend/legacy-src/`:
- `main.tsx`
- `App.tsx`
- `App.simple.tsx`
- `App.auth.tsx`
- `TestApp.tsx`
- `debug.tsx`
- `simple.js`

This keeps them available for historical reference while removing them from the
active TypeScript source tree.

### Remaining recommendation
Delete `legacy-src/` entirely once you are confident no further historical
reference is needed.

## 4. Dependency truth

`frontend/package.json` still contains packages from multiple architectural eras,
including React Router dependencies despite the current App Router direction.

### Recommendation
Run a dependency review and remove packages that are no longer needed after the
App Router migration is fully complete.
