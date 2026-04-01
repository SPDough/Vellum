"""
State Street Custodian API specification.

Source document: State Street Core Data Consumption Model – Custody Accounting v10
  File: v10_State_Street_Core_Data_Consumption_Model__Custody_Accounting_2026_02_14.xlsx
  Ingest key: custody_api (backend/app/rag/ingest.py DOCUMENTS["custody_api"])
  Path: data/raw/v10_State_Street_Core_Data_Consumption_Model__Custody_Accounting_2026_02_14.xlsx

The Excel defines consumption marts (e.g. ENTITY_NAV, TRANSACTION, POSITION_LOT) in the
"Consumption Mart Dictionary" and "API Listing" sheets. Capability ids below can be
aligned with mart names or API listing endpoints from that document.
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
    source_document: Optional[str] = None  # e.g. Excel filename or ingest key
    capability_aliases: Optional[Dict[str, str]] = None  # e.g. {"positions": "position_lot"}

    def get_capability(self, capability_id: str) -> Optional[ApiCapability]:
        resolved_id = (self.capability_aliases or {}).get(capability_id, capability_id)
        for cap in self.capabilities:
            if cap.id == resolved_id:
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
                "query_params": c.query_params,
            }
            for c in self.capabilities
        ]


# State Street Custodian API spec — aligned with Core Data Consumption Model v10 (Custody Accounting).
# Data marts and fields from Consumption Mart Dictionary; FIELD NAME → query_params, DATA TYPE, NULLABLE, DESCRIPTION.
STATE_STREET_CUSTODY_API_SOURCE_FILE = "v10_State_Street_Core_Data_Consumption_Model__Custody_Accounting_2026_02_14.xlsx"
# Backward compatibility: old capability ids → new data-mart ids
STATE_STREET_CAPABILITY_ALIASES = {
    "positions": "position_lot",
    "transactions": "transaction",
    "cash_balances": "cash_balance",
    "corporate_actions": "corporate_action",
}
STATE_STREET_API_SPEC = CustodianApiSpec(
    custodian_id="state_street",
    display_name="State Street Global Services",
    base_url="https://api.statestreet.com/v1",
    auth_type="bearer",
    version="10",
    docs_url=None,
    source_document=STATE_STREET_CUSTODY_API_SOURCE_FILE,
    capability_aliases=STATE_STREET_CAPABILITY_ALIASES,
    capabilities=[
        ApiCapability(
            id="entity_nav",
            name="ENTITY_NAV",
            description="Net Asset Value for an entity; position or valuation as of a date.",
            path="/entity-nav",
            method="GET",
            query_params=[
                {"name": "account_id", "type": "string", "required": True, "description": "Unique identifier for the account"},
                {"name": "as_of_date", "type": "string", "required": True, "description": "Date of the current position or valuation", "format": "DATE"},
                {"name": "instrument_id", "type": "string", "required": False, "description": "Security or instrument identifier"},
                {"name": "currency_code", "type": "string", "required": False, "description": "ISO currency code", "max_length": 3},
            ],
        ),
        ApiCapability(
            id="transaction",
            name="TRANSACTION",
            description="Details of financial transactions (settlements, income, movements).",
            path="/transaction",
            method="GET",
            query_params=[
                {"name": "account_id", "type": "string", "required": True, "description": "Unique identifier for the account"},
                {"name": "transaction_id", "type": "string", "required": False, "description": "Unique identifier for the transaction"},
                {"name": "from_date", "type": "string", "required": False, "description": "Start date for transaction range", "format": "DATE"},
                {"name": "to_date", "type": "string", "required": False, "description": "End date for transaction range", "format": "DATE"},
                {"name": "gross_amount", "type": "number", "required": False, "description": "Monetary amount of the transaction"},
            ],
        ),
        ApiCapability(
            id="position_lot",
            name="POSITION_LOT",
            description="Specific lots of positions held (quantity, cost basis per lot).",
            path="/position-lot",
            method="GET",
            query_params=[
                {"name": "account_id", "type": "string", "required": True, "description": "Unique identifier for the account"},
                {"name": "as_of_date", "type": "string", "required": True, "description": "Date of the current position", "format": "DATE"},
                {"name": "lot_id", "type": "string", "required": False, "description": "Identifier for the lot"},
                {"name": "instrument_id", "type": "string", "required": False, "description": "Security or instrument identifier"},
                {"name": "quantity", "type": "number", "required": False, "description": "Quantity held in the lot"},
                {"name": "cost_basis", "type": "number", "required": False, "description": "Cost basis for the lot"},
            ],
        ),
        ApiCapability(
            id="trade",
            name="TRADE",
            description="Trade details (executions, trade date, settlement).",
            path="/trade",
            method="GET",
            query_params=[
                {"name": "account_id", "type": "string", "required": True, "description": "Unique identifier for the account"},
                {"name": "trade_id", "type": "string", "required": False, "description": "Unique identifier for the trade"},
                {"name": "trade_date", "type": "string", "required": False, "description": "Date of the trade", "format": "DATE"},
                {"name": "from_date", "type": "string", "required": False, "description": "Start date for trade range", "format": "DATE"},
                {"name": "to_date", "type": "string", "required": False, "description": "End date for trade range", "format": "DATE"},
            ],
        ),
        ApiCapability(
            id="corporate_action",
            name="CORPORATE_ACTION",
            description="Corporate action events (dividends, reorgs, splits).",
            path="/corporate-action",
            method="GET",
            query_params=[
                {"name": "account_id", "type": "string", "required": False, "description": "Unique identifier for the account"},
                {"name": "corporate_action_type", "type": "string", "required": False, "description": "Code representing the type of corporate action"},
                {"name": "from_date", "type": "string", "required": False, "description": "Start date for event range", "format": "DATE"},
                {"name": "to_date", "type": "string", "required": False, "description": "End date for event range", "format": "DATE"},
            ],
        ),
        ApiCapability(
            id="general_ledger",
            name="GENERAL_LEDGER",
            description="General ledger entries (journal entries, GL account balances).",
            path="/general-ledger",
            method="GET",
            query_params=[
                {"name": "account_id", "type": "string", "required": False, "description": "Unique identifier for the account"},
                {"name": "gl_account_number", "type": "string", "required": False, "description": "General ledger account number"},
                {"name": "as_of_date", "type": "string", "required": False, "description": "Date of the ledger position", "format": "DATE"},
                {"name": "from_date", "type": "string", "required": False, "description": "Start date for entries", "format": "DATE"},
                {"name": "to_date", "type": "string", "required": False, "description": "End date for entries", "format": "DATE"},
            ],
        ),
        ApiCapability(
            id="cash_balance",
            name="CASH_BALANCE",
            description="Cash balances by account and currency as of a date.",
            path="/cash-balance",
            method="GET",
            query_params=[
                {"name": "account_id", "type": "string", "required": True, "description": "Unique identifier for the account"},
                {"name": "as_of_date", "type": "string", "required": True, "description": "Date of the balance", "format": "DATE"},
                {"name": "currency_code", "type": "string", "required": False, "description": "ISO currency code", "max_length": 3},
                {"name": "balance_amount", "type": "number", "required": False, "description": "Monetary balance amount"},
            ],
        ),
        ApiCapability(
            id="cash_flow",
            name="CASH_FLOW",
            description="Cash flow events (inflows, outflows, movements).",
            path="/cash-flow",
            method="GET",
            query_params=[
                {"name": "account_id", "type": "string", "required": True, "description": "Unique identifier for the account"},
                {"name": "from_date", "type": "string", "required": False, "description": "Start date for cash flow range", "format": "DATE"},
                {"name": "to_date", "type": "string", "required": False, "description": "End date for cash flow range", "format": "DATE"},
            ],
        ),
    ],
)


def get_state_street_capabilities() -> List[Dict[str, Any]]:
    """Return State Street capabilities for API responses."""
    return STATE_STREET_API_SPEC.to_capabilities_list()
