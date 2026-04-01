"""Bootstrap registration for generalized integration providers."""

from __future__ import annotations

from app.core.config import get_settings
from app.integrations.providers.state_street.config import StateStreetConfig
from app.integrations.providers.state_street.provider import StateStreetProvider
from app.integrations.registry.providers import provider_registry


def register_default_providers() -> None:
    settings = get_settings()

    if settings.integrations_enabled:
        state_street_provider = StateStreetProvider(
            config=StateStreetConfig(
                enabled=settings.state_street_enabled,
                base_url=settings.state_street_base_url,
                auth_url=settings.state_street_auth_url,
                client_id=settings.state_street_client_id,
                client_secret=settings.state_street_client_secret,
                api_key=settings.state_street_api_key,
                timeout_seconds=settings.state_street_timeout_seconds,
                environment=settings.state_street_environment,
            )
        )
        provider_registry.register(state_street_provider)
