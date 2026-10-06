"""Deprecated: use app.core.jwt_auth.JwtAuthMiddleware (P2).

Retained so older imports keep working.
"""

from app.core.jwt_auth import JwtAuthMiddleware as PlaceholderAuthMiddleware

__all__ = ["PlaceholderAuthMiddleware"]
