"""Tool registry helpers for provider-backed generic tools."""

from __future__ import annotations

from typing import Any, Dict

from .providers import provider_registry


def execute_provider_tool(provider_id: str, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
    provider = provider_registry.get(provider_id)
    if not provider:
        raise ValueError(f'Unknown provider: {provider_id}')
    return provider.execute_tool(tool_name, **kwargs)
