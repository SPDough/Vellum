"""Non-operational placeholder until JWT / Keycloak auth is fully wired."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class PlaceholderAuthMiddleware(BaseHTTPMiddleware):
    """
    Sets `request.state.auth_subject` for downstream handlers.

    If an `Authorization: Bearer ...` header is present, a distinct placeholder subject
    is used so call sites can tell the header was seen (still not validated).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        subject = "placeholder-user@vellum.ops"
        auth = request.headers.get("authorization") or request.headers.get(
            "Authorization"
        )
        if auth and auth.lower().startswith("bearer "):
            subject = "bearer-subject-placeholder@vellum.ops"
        request.state.auth_subject = subject
        return await call_next(request)
