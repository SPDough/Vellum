"""JWT request authentication middleware (replaces placeholder auth).

Validates HS256 access tokens issued by the simple AuthService.
In non-production, AUTH_REQUIRED=false allows anonymous access for local DX
while still rejecting *invalid* Bearer tokens when present.
"""

from __future__ import annotations

from typing import Optional

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings

# Paths that never require auth (health / docs / CORS preflight handled separately).
_PUBLIC_PATH_PREFIXES = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/auth/providers",
)


def _is_public(path: str) -> bool:
    if path == "/":
        return True
    return any(path == p or path.startswith(p + "/") for p in _PUBLIC_PATH_PREFIXES)


def decode_access_token(token: str) -> Optional[dict]:
    settings = get_settings()
    secret = settings.secret_key
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "access":
        return None
    return payload


class JwtAuthMiddleware(BaseHTTPMiddleware):
    """
    Sets `request.state.auth_subject` from a validated JWT.

    Behavior:
    - No Authorization header:
        - allow if auth_required is False (dev/test default)
        - 401 if auth_required is True (production default)
    - Invalid/expired Bearer token: always 401
    - Valid Bearer token: subject from email/sub/user_id claims
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        path = request.url.path
        auth_required = bool(
            settings.auth_required or settings.environment == "production"
        )

        if request.method == "OPTIONS" or _is_public(path):
            request.state.auth_subject = "anonymous@vellum.ops"
            return await call_next(request)

        auth = request.headers.get("authorization") or request.headers.get(
            "Authorization"
        )
        token: Optional[str] = None
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()

        if not token:
            if auth_required:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Not authenticated"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            request.state.auth_subject = "anonymous@vellum.ops"
            return await call_next(request)

        payload = decode_access_token(token)
        if payload is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired access token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        subject = (
            payload.get("email")
            or payload.get("sub")
            or payload.get("user_id")
            or payload.get("username")
            or "authenticated@vellum.ops"
        )
        request.state.auth_subject = str(subject)
        request.state.auth_claims = payload
        return await call_next(request)
