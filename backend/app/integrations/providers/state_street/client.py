"""State Street API client scaffold."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.integrations.base.client import BaseIntegrationClient
from .auth import StateStreetAuthStrategy
from .config import StateStreetConfig


class StateStreetClient(BaseIntegrationClient):
    def __init__(self, config: StateStreetConfig, token: Optional[str] = None):
        super().__init__(
            base_url=config.base_url,
            auth_strategy=StateStreetAuthStrategy(token=token),
            timeout_seconds=config.timeout_seconds,
        )
        self.config = config

    def get_positions(self, params: Optional[Dict[str, Any]] = None):
        return self.get('/custody-position/v1/quantity-positions', params=params)

    def get_cash_activity(self, params: Optional[Dict[str, Any]] = None):
        return self.get('/custody-cash/v1/activities', params=params)

    def get_trade_status(self, params: Optional[Dict[str, Any]] = None):
        return self.get('/custody-trade/v2/status', params=params)
