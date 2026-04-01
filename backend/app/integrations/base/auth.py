"""Authentication abstractions for external integration providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict


class AuthStrategy(ABC):
    """Base authentication strategy."""

    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """Return request headers for provider authentication."""


class ApiKeyAuth(AuthStrategy):
    def __init__(self, header_name: str, api_key: str):
        self.header_name = header_name
        self.api_key = api_key

    def get_headers(self) -> Dict[str, str]:
        return {self.header_name: self.api_key}


class BearerTokenAuth(AuthStrategy):
    def __init__(self, token: str):
        self.token = token

    def get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


class OAuthClientCredentialsAuth(AuthStrategy):
    """Placeholder for future provider OAuth client credentials support."""

    def __init__(self, token: str = ""):
        self.token = token

    def get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}
