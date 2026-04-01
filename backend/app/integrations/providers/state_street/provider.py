"""State Street provider registration scaffold."""

from __future__ import annotations

from typing import Any, Dict, List

from app.integrations.base.models import ProviderDescriptor, ProviderHealth, ProviderStatus
from app.integrations.base.provider import IntegrationProvider
from .client import StateStreetClient
from .config import StateStreetConfig
from .tools import StateStreetTools


class StateStreetProvider(IntegrationProvider):
    def __init__(self, config: StateStreetConfig | None = None):
        self.config = config or StateStreetConfig()
        self.client = StateStreetClient(self.config)
        self.tools = StateStreetTools(self.client)
        self._descriptor = ProviderDescriptor(
            provider_id='state_street',
            display_name='State Street',
            vendor_type='custodian',
            supported_domains=['custody', 'fund_accounting'],
            supported_tools=['get_positions', 'get_cash_activity', 'get_trade_status'],
            auth_strategy_type='state_street_placeholder',
            enabled=self.config.enabled,
            metadata={
                'provider_family': 'custodian',
                'first_provider': True,
            },
        )

    @property
    def descriptor(self) -> ProviderDescriptor:
        return self._descriptor

    def get_supported_tools(self) -> List[str]:
        return self.descriptor.supported_tools

    def get_status(self) -> ProviderStatus:
        return ProviderStatus(
            provider_id=self.descriptor.provider_id,
            enabled=self.config.enabled,
            configured=bool(self.config.base_url),
            healthy=False,
            message='Architecture scaffold created; live API not connected yet.',
        )

    def get_health(self) -> ProviderHealth:
        return ProviderHealth(
            provider_id=self.descriptor.provider_id,
            healthy=False,
            checks={'live_api_connected': False},
            message='State Street provider scaffold is present but not live-enabled.',
        )

    def execute_tool(self, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        if tool_name == 'get_positions':
            return self.tools.get_positions(kwargs or None)
        if tool_name == 'get_cash_activity':
            return self.tools.get_cash_activity(kwargs or None)
        if tool_name == 'get_trade_status':
            return self.tools.get_trade_status(kwargs or None)
        raise ValueError(f'Unsupported State Street tool: {tool_name}')
