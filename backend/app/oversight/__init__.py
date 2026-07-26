"""Custodian oversight vertical slice: fixtures → contracts → JSON rules → breaks."""

from app.oversight.service import OversightService, get_oversight_service

__all__ = ["OversightService", "get_oversight_service"]
