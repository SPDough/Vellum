"""Common models for provider metadata and health/state tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProviderCapability:
    """Describes a generic domain/tool capability offered by a provider."""

    name: str
    description: str
    domain: str


@dataclass
class ProviderDescriptor:
    """Metadata that identifies and describes an integration provider."""

    provider_id: str
    display_name: str
    vendor_type: str
    supported_domains: List[str] = field(default_factory=list)
    supported_tools: List[str] = field(default_factory=list)
    auth_strategy_type: Optional[str] = None
    enabled: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderStatus:
    """Current status snapshot for a provider instance."""

    provider_id: str
    enabled: bool
    configured: bool
    healthy: bool
    message: Optional[str] = None


@dataclass
class ProviderHealth:
    """Health details for a provider or provider connection."""

    provider_id: str
    healthy: bool
    checks: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None
