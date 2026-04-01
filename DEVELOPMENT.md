# Development Guide

This guide describes the current intended local development flows for `Vellum-main`.

## First-pass development truth

The repository currently contains both:

- a **full backend** at `backend/app/main.py`
- a **demo/dev backend** at `backend/app/main_simple.py`
- a **canonical frontend path** using **Next.js App Router** in `frontend/app/*`
- legacy SPA-style frontend files retained temporarily for migration reference

The goal of this guide is to make those paths explicit.

## Recommended local workflows

## Option 1: Demo mode (fastest local path)

Use this when you want quick local iteration without standing up the full infrastructure stack.

### Backend
```bash
cd backend
python app/main_simple.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Notes
- backend: http://localhost:8000
- frontend: http://localhost:3000
- this mode is intended for demos and lightweight local work
- `main_simple.py` is not the primary production backend entrypoint

## Option 2: Full-backend development mode

Use this when working against the intended real backend architecture.

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Notes
- intended primary API contract: `/api/v1/...`
- frontend target architecture: Next.js App Router
- depending on your environment, the full backend may require additional infrastructure and configuration

## Frontend architecture note

The intended frontend runtime is the Next.js App Router under:

- `frontend/app/layout.tsx`
- `frontend/app/page.tsx`
- `frontend/app/**/page.tsx`

Legacy SPA-style files such as `frontend/src/main.tsx` and `frontend/src/App.tsx` are retained temporarily for migration reference only. They should not be treated as the primary runtime path for new work.

## Auth / API note

The long-term target application contract is:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/refresh`

The demo backend currently uses simplified `/api/auth/...` routes for convenience. Those routes are part of demo mode, not the intended long-term primary application contract.

## Testing

Current tests in the repository include a mix of lightweight/demo-oriented and broader integration-oriented coverage.

### Backend tests
```bash
cd backend
python -m pytest tests/ -q
```

### Frontend tests
```bash
cd frontend
npm run test:run
```

## Linting and type checks

### Frontend
```bash
cd frontend
npm run lint
```

### Backend
```bash
cd backend
python -m black --check .
python -m isort --check-only .
```

## Troubleshooting

### Port already in use
```bash
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

### Missing frontend dependencies
```bash
cd frontend && npm install
```

### Missing backend dependencies
```bash
cd backend && pip install -r requirements.txt
```

## Additional architecture references

- [`ARCHITECTURE.md`](ARCHITECTURE.md)
- [`RUN_MODES.md`](RUN_MODES.md)
- [`AUTH_STRATEGY.md`](AUTH_STRATEGY.md)
