"""Helpers for inspecting available contracts."""

from __future__ import annotations

from typing import Any, Dict

from .registry import get_contract_registry


def list_registered_contracts() -> Dict[str, Any]:
    registry = get_contract_registry()
    return registry.list_contracts()
