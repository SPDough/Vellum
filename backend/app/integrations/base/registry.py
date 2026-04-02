"""Provider registry for generalized external integrations."""

from __future__ import annotations

from typing import Dict, List, Optional

from .provider import IntegrationProvider


class ProviderRegistry:
    """Simple in-memory registry for integration providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, IntegrationProvider] = {}

    def register(self, provider: IntegrationProvider) -> None:
        self._providers[provider.descriptor.provider_id] = provider

    def get(self, provider_id: str) -> Optional[IntegrationProvider]:
        return self._providers.get(provider_id)

    def list_provider_ids(self) -> List[str]:
        return list(self._providers.keys())

    def list_providers(self) -> List[IntegrationProvider]:
        return list(self._providers.values())
