"""Reusable HTTP client scaffold for integration providers."""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from .auth import AuthStrategy


class BaseIntegrationClient:
    """Minimal reusable HTTP client for provider implementations."""

    def __init__(self, base_url: str, auth_strategy: Optional[AuthStrategy] = None, timeout_seconds: int = 30):
        self.base_url = base_url.rstrip('/')
        self.auth_strategy = auth_strategy
        self.timeout_seconds = timeout_seconds

    def build_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.auth_strategy:
            headers.update(self.auth_strategy.get_headers())
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None):
        return requests.get(
            f"{self.base_url}/{path.lstrip('/')}",
            params=params,
            headers=self.build_headers(headers),
            timeout=self.timeout_seconds,
        )
