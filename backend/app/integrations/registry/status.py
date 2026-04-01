"""Helper functions for provider status inspection."""

from __future__ import annotations

from typing import Any, Dict, List

from .providers import provider_registry


def list_provider_status() -> List[Dict[str, Any]]:
    return [
        {
            'provider_id': provider.descriptor.provider_id,
            'display_name': provider.descriptor.display_name,
            'status': provider.get_status().__dict__,
            'health': provider.get_health().__dict__,
        }
        for provider in provider_registry.list_providers()
    ]
