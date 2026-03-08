"""
Custodian API specifications.

Each custodian module defines capabilities (endpoints, auth, and metadata)
so the app can list and call custodian APIs in a consistent way.
Specs can be updated from official custodian API documentation.
"""

from app.services.custodian_apis.state_street import (
    STATE_STREET_API_SPEC,
    get_state_street_capabilities,
)

__all__ = [
    "STATE_STREET_API_SPEC",
    "get_state_street_capabilities",
    "get_custodian_api_spec",
    "list_custodian_api_specs",
]


def get_custodian_api_spec(custodian_id: str):
    """Return the API spec for a custodian, or None if not defined."""
    specs = {
        "state_street": STATE_STREET_API_SPEC,
    }
    return specs.get(custodian_id)


def list_custodian_api_specs():
    """Return list of custodian IDs that have an API spec."""
    return ["state_street"]
