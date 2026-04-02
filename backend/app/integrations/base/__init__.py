"""Base integration framework primitives for external provider support."""

from .exceptions import (
    IntegrationError,
    ProviderAuthError,
    ProviderConfigError,
    ProviderRateLimitError,
    ProviderResponseError,
)
from .models import ProviderCapability, ProviderDescriptor, ProviderHealth, ProviderStatus
from .provider import IntegrationProvider
from .registry import ProviderRegistry

__all__ = [
    'IntegrationError',
    'ProviderAuthError',
    'ProviderConfigError',
    'ProviderRateLimitError',
    'ProviderResponseError',
    'ProviderCapability',
    'ProviderDescriptor',
    'ProviderHealth',
    'ProviderStatus',
    'IntegrationProvider',
    'ProviderRegistry',
]
