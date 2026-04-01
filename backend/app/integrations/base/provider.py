"""Base provider contract for generalized external integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .models import ProviderDescriptor, ProviderHealth, ProviderStatus


class IntegrationProvider(ABC):
    """Abstract base class for integration providers."""

    @property
    @abstractmethod
    def descriptor(self) -> ProviderDescriptor:
        """Return provider metadata."""

    @abstractmethod
    def get_supported_tools(self) -> List[str]:
        """Return tool names supported by this provider."""

    @abstractmethod
    def get_status(self) -> ProviderStatus:
        """Return current provider status."""

    @abstractmethod
    def get_health(self) -> ProviderHealth:
        """Return provider health details."""

    @abstractmethod
    def execute_tool(self, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a generic integration tool exposed by this provider."""
