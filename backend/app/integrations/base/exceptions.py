"""Exception taxonomy for the generalized integration framework."""


class IntegrationError(Exception):
    """Base exception for integration framework errors."""


class ProviderConfigError(IntegrationError):
    """Raised when a provider is misconfigured or missing required settings."""


class ProviderAuthError(IntegrationError):
    """Raised when provider authentication fails."""


class ProviderRateLimitError(IntegrationError):
    """Raised when a provider request is rate limited."""


class ProviderResponseError(IntegrationError):
    """Raised when a provider returns an invalid or unusable response."""
