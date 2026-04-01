"""State Street-specific configuration scaffold."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class StateStreetConfig:
    enabled: bool = False
    base_url: str = 'https://api.statestr.com'
    auth_url: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    api_key: Optional[str] = None
    timeout_seconds: int = 30
    environment: str = 'sandbox'
