# Auth Strategy

This document captures the first-pass auth direction for `Vellum-main`.

## Current problem

The repository currently mixes multiple auth assumptions:

- frontend code that directly calls `http://localhost:8000/api/auth/...`
- backend routes in the full app mounted under `/api/v1/...`
- a simplified backend that exposes `/api/auth/...` demo endpoints
- additional Keycloak / enterprise auth code paths

This creates confusion about what the real auth contract actually is.

## First-pass decision

The target long-term application contract is:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/refresh`

## Demo auth vs real auth

### Demo auth
- Implemented in `backend/app/main_simple.py`
- Intended for local demo/dev convenience
- Uses simplified demo credentials and lightweight token behavior
- May continue to expose `/api/auth/...` routes for demo compatibility

### Real auth
- Intended to be handled by the full backend route stack under `/api/v1/auth/...`
- This is the contract frontend integration should move toward

## Frontend rule

Frontend code should not hardcode direct auth URLs like:

- `http://localhost:8000/api/auth/login`
- `http://localhost:8000/api/auth/me`
- `http://localhost:8000/api/auth/logout`

Instead, auth traffic should go through the shared API client and follow the configured base URL.

## Token handling rule

The frontend should standardize on a single token storage convention. First-pass cleanup aligns toward:

- `access_token`
- `refresh_token`

and `Authorization: Bearer <token>` for authenticated requests.

## Deferred work

Deferred to later passes:

- selecting whether Keycloak is active now or deferred
- unifying all auth service abstractions
- tightening real auth behavior and refresh flows
- deleting legacy/demo-only auth compatibility code
