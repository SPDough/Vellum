"""Integration-backed source registration placeholders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class IntegrationSourceRegistration:
    provider_id: str
    source_name: str
    domain: str
    description: Optional[str] = None
