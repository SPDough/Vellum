"""State Street auth scaffold.

Auth details are intentionally left as placeholders until the live State Street
portal/auth contract is confirmed.
"""

from __future__ import annotations

from typing import Optional

from app.integrations.base.auth import AuthStrategy, BearerTokenAuth


class StateStreetAuthStrategy(AuthStrategy):
    def __init__(self, token: Optional[str] = None):
        self.token = token

    def get_headers(self):
        if not self.token:
            return {}
        return BearerTokenAuth(self.token).get_headers()
