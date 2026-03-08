"""
State Street Custodian API specification.

Define endpoints and capabilities from the State Street Custodian API document.
Update base_url, auth_type, and capabilities to match your official API spec.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ApiCapability:
    """A single API capability (endpoint) offered by the custodian."""

    id: str
    name: str
    description: str
    path: str
    method: str = "GET"
    query_params: Optional[List[Dict[str, Any]]] = None
    body_schema: Optional[Dict[str, Any]] = None


@dataclass
class CustodianApiSpec:
    """Full API specification for a custodian."""

    custodian_id: str
    display_name: str
    base_url: str
    auth_type: str
    capabilities: List[ApiCapability] = field(default_factory=list)
    docs_url: Optional[str] = None
    version: Optional[str] = None

    def get_capability(self, capability_id: str) -> Optional[ApiCapability]:
        for cap in self.capabilities:
            if cap.id == capability_id:
                return cap
        return None

    def to_capabilities_list(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "path": c.path,
                "method": c.method,
            }
            for c in self.capabilities
        ]


# State Street Custodian API spec — update from your API document
STATE_STREET_API_SPEC = CustodianApiSpec(
    custodian_id="state_street",
    display_name="State Street Global Services",
    base_url="https://api.statestreet.com/v1",
    auth_type="bearer",
    version="1.0",
    docs_url=None,
    capabilities=[
        ApiCapability(
            id="positions",
            name="Positions",
            description="Retrieve account positions",
            path="/positions",
            method="GET",
            query_params=[
                {"name": "account_id", "type": "string", "required": True},
                {"name": "as_of_date", "type": "string", "required": False},
            ],
        ),
        ApiCapability(
            id="transactions",
            name="Transactions",
            description="Retrieve account transactions",
            path="/transactions",
            method="GET",
            query_params=[
                {"name": "account_id", "type": "string", "required": True},
                {"name": "from_date", "type": "string", "required": False},
                {"name": "to_date", "type": "string", "required": False},
            ],
        ),
        ApiCapability(
            id="cash_balances",
            name="Cash Balances",
            description="Retrieve cash balances",
            path="/cash-balances",
            method="GET",
            query_params=[
                {"name": "account_id", "type": "string", "required": True},
                {"name": "as_of_date", "type": "string", "required": False},
            ],
        ),
        ApiCapability(
            id="corporate_actions",
            name="Corporate Actions",
            description="Retrieve corporate action events",
            path="/corporate-actions",
            method="GET",
            query_params=[
                {"name": "account_id", "type": "string", "required": False},
                {"name": "from_date", "type": "string", "required": False},
                {"name": "to_date", "type": "string", "required": False},
            ],
        ),
    ],
)


def get_state_street_capabilities() -> List[Dict[str, Any]]:
    """Return State Street capabilities for API responses."""
    return STATE_STREET_API_SPEC.to_capabilities_list()
