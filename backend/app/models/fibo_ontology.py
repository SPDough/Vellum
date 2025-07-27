from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .knowledge_graph import BaseEntity, BaseRelationship, EntityType, RelationshipType


class FIBOEntityType(str, Enum):
    """FIBO-compliant entity types following Financial Industry Business Ontology."""

    LEGAL_ENTITY = "LegalEntity"
    ORGANIZATION = "Organization"
    PERSON = "Person"

    FINANCIAL_INSTRUMENT = "FinancialInstrument"
    EQUITY_INSTRUMENT = "EquityInstrument"
    DEBT_INSTRUMENT = "DebtInstrument"
    DERIVATIVE_INSTRUMENT = "DerivativeInstrument"

    FINANCIAL_ACCOUNT = "FinancialAccount"
    CUSTODY_ACCOUNT = "CustodyAccount"
    TRADING_ACCOUNT = "TradingAccount"
    POSITION_HOLDING = "PositionHolding"

    MARKET = "Market"
    EXCHANGE = "Exchange"
    TRADING_VENUE = "TradingVenue"
    CLEARING_HOUSE = "ClearingHouse"

    FINANCIAL_TRANSACTION = "FinancialTransaction"
    TRADE_TRANSACTION = "TradeTransaction"
    SETTLEMENT_TRANSACTION = "SettlementTransaction"

    COUNTERPARTY_ROLE = "CounterpartyRole"
    CUSTODIAN_ROLE = "CustodianRole"
    INVESTMENT_MANAGER_ROLE = "InvestmentManagerRole"

    FINANCIAL_IDENTIFIER = "FinancialIdentifier"
    ISIN_IDENTIFIER = "ISINIdentifier"
    CUSIP_IDENTIFIER = "CUSIPIdentifier"


class FIBORelationshipType(str, Enum):
    """FIBO-compliant relationship types."""

    HAS_IDENTIFIER = "hasIdentifier"
    IS_IDENTIFIED_BY = "isIdentifiedBy"
    HAS_HOLDING = "hasHolding"
    IS_HELD_BY = "isHeldBy"

    PLAYS_ROLE = "playsRole"
    IS_ROLE_OF = "isRoleOf"
    HAS_COUNTERPARTY = "hasCounterparty"

    IS_TRANSACTION_IN = "isTransactionIn"
    SETTLES_VIA = "settlesVia"
    CLEARS_THROUGH = "clearsThrough"

    IS_TRADED_ON = "isTradedOn"
    IS_LISTED_ON = "isListedOn"

    HAS_EFFECTIVE_DATE = "hasEffectiveDate"
    HAS_MATURITY_DATE = "hasMaturityDate"


class FIBOLegalEntity(BaseEntity):
    """FIBO Legal Entity - represents organizations with legal standing."""

    entity_type: EntityType = EntityType.COUNTERPARTY
    fibo_type: FIBOEntityType = FIBOEntityType.LEGAL_ENTITY

    legal_name: str
    legal_jurisdiction: str
    lei_code: Optional[str] = None  # Legal Entity Identifier
    registration_number: Optional[str] = None
    legal_form: Optional[str] = None  # e.g., "Corporation", "Partnership"

    class Config:
        schema_extra = {
            "example": {
                "id": "le_state_street",
                "name": "State Street Corporation",
                "legal_name": "State Street Corporation",
                "legal_jurisdiction": "US-MA",
                "lei_code": "571474TGEMMWANRLN572",
                "legal_form": "Corporation",
            }
        }


class FIBOFinancialInstrument(BaseEntity):
    """FIBO Financial Instrument - base class for all tradeable instruments."""

    entity_type: EntityType = EntityType.SECURITY
    fibo_type: FIBOEntityType = FIBOEntityType.FINANCIAL_INSTRUMENT

    instrument_name: str
    instrument_type: str
    currency_denomination: str
    issue_date: Optional[datetime] = None
    maturity_date: Optional[datetime] = None

    primary_identifier: Optional[str] = None
    identifier_scheme: Optional[str] = None  # "ISIN", "CUSIP", "SEDOL"

    class Config:
        schema_extra = {
            "example": {
                "id": "fi_aapl_equity",
                "name": "Apple Inc. Common Stock",
                "instrument_name": "Apple Inc. Common Stock",
                "instrument_type": "EQUITY",
                "currency_denomination": "USD",
                "primary_identifier": "US0378331005",
                "identifier_scheme": "ISIN",
            }
        }


class FIBOEquityInstrument(FIBOFinancialInstrument):
    """FIBO Equity Instrument - represents ownership stakes."""

    fibo_type: FIBOEntityType = FIBOEntityType.EQUITY_INSTRUMENT

    shares_outstanding: Optional[int] = None
    par_value: Optional[float] = None
    dividend_type: Optional[str] = None  # "COMMON", "PREFERRED"
    voting_rights: bool = True

    class Config:
        schema_extra = {
            "example": {
                "id": "eq_aapl",
                "name": "Apple Inc. Common Stock",
                "instrument_name": "Apple Inc. Common Stock",
                "instrument_type": "EQUITY",
                "currency_denomination": "USD",
                "shares_outstanding": 15728700000,
                "dividend_type": "COMMON",
                "voting_rights": True,
            }
        }


class FIBODebtInstrument(FIBOFinancialInstrument):
    """FIBO Debt Instrument - represents debt obligations."""

    fibo_type: FIBOEntityType = FIBOEntityType.DEBT_INSTRUMENT

    principal_amount: float
    coupon_rate: Optional[float] = None
    payment_frequency: Optional[str] = None  # "QUARTERLY", "SEMI_ANNUAL", "ANNUAL"
    credit_rating: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "debt_us_10y",
                "name": "US Treasury 10-Year Note",
                "instrument_name": "US Treasury 10-Year Note",
                "instrument_type": "GOVERNMENT_BOND",
                "currency_denomination": "USD",
                "principal_amount": 1000.0,
                "coupon_rate": 0.025,
                "payment_frequency": "SEMI_ANNUAL",
            }
        }


class FIBOFinancialAccount(BaseEntity):
    """FIBO Financial Account - represents accounts holding financial positions."""

    entity_type: EntityType = EntityType.ACCOUNT
    fibo_type: FIBOEntityType = FIBOEntityType.FINANCIAL_ACCOUNT

    account_identifier: str
    account_purpose: str  # "CUSTODY", "TRADING", "SETTLEMENT"
    base_currency: str
    account_status: str = "ACTIVE"

    account_holder_id: str  # Legal Entity ID
    custodian_id: Optional[str] = None  # Custodian Legal Entity ID

    class Config:
        schema_extra = {
            "example": {
                "id": "fa_custody_001",
                "name": "Global Equity Fund Custody Account",
                "account_identifier": "CUST123456789",
                "account_purpose": "CUSTODY",
                "base_currency": "USD",
                "account_holder_id": "le_global_equity_fund",
                "custodian_id": "le_state_street",
            }
        }


class FIBOPositionHolding(BaseEntity):
    """FIBO Position Holding - represents holdings of financial instruments."""

    entity_type: EntityType = EntityType.POSITION
    fibo_type: FIBOEntityType = FIBOEntityType.POSITION_HOLDING

    holding_quantity: float
    holding_value: float
    cost_basis: float
    holding_date: datetime

    held_instrument_id: str  # Financial Instrument ID
    holding_account_id: str  # Financial Account ID

    class Config:
        schema_extra = {
            "example": {
                "id": "ph_aapl_holding",
                "name": "Apple Inc. Position Holding",
                "holding_quantity": 1000.0,
                "holding_value": 150000.0,
                "cost_basis": 145000.0,
                "held_instrument_id": "fi_aapl_equity",
                "holding_account_id": "fa_custody_001",
            }
        }


class FIBOTradeTransaction(BaseEntity):
    """FIBO Trade Transaction - represents executed trades."""

    entity_type: EntityType = EntityType.TRADE
    fibo_type: FIBOEntityType = FIBOEntityType.TRADE_TRANSACTION

    transaction_identifier: str
    transaction_date: datetime
    settlement_date: datetime
    transaction_type: str  # "BUY", "SELL"

    quantity_transacted: float
    transaction_price: float
    transaction_amount: float

    transacted_instrument_id: str
    transaction_account_id: str
    counterparty_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "tt_aapl_buy_001",
                "name": "Apple Inc. Purchase Transaction",
                "transaction_identifier": "TXN123456",
                "transaction_type": "BUY",
                "quantity_transacted": 1000.0,
                "transaction_price": 150.0,
                "transaction_amount": 150000.0,
                "transacted_instrument_id": "fi_aapl_equity",
                "transaction_account_id": "fa_custody_001",
            }
        }


class FIBOHasHoldingRelationship(BaseRelationship):
    """FIBO relationship: Account has holding of instrument."""

    relationship_type: RelationshipType = RelationshipType.HOLDS
    fibo_relationship_type: FIBORelationshipType = FIBORelationshipType.HAS_HOLDING

    holding_percentage: Optional[float] = None
    holding_date: datetime

    class Config:
        schema_extra = {
            "example": {
                "relationship_type": "HOLDS",
                "fibo_relationship_type": "hasHolding",
                "from_entity_id": "fa_custody_001",
                "to_entity_id": "ph_aapl_holding",
                "holding_percentage": 2.5,
            }
        }


class FIBOPlaysRoleRelationship(BaseRelationship):
    """FIBO relationship: Legal Entity plays a role."""

    relationship_type: RelationshipType = RelationshipType.MANAGES
    fibo_relationship_type: FIBORelationshipType = FIBORelationshipType.PLAYS_ROLE

    role_type: str  # "CUSTODIAN", "INVESTMENT_MANAGER", "COUNTERPARTY"
    role_start_date: datetime
    role_end_date: Optional[datetime] = None

    class Config:
        schema_extra = {
            "example": {
                "relationship_type": "MANAGES",
                "fibo_relationship_type": "playsRole",
                "from_entity_id": "le_state_street",
                "to_entity_id": "fa_custody_001",
                "role_type": "CUSTODIAN",
            }
        }


class FIBOOntologyMapping(BaseModel):
    """Mapping between existing entities and FIBO ontology."""

    source_entity_id: str
    source_entity_type: EntityType
    fibo_entity_type: FIBOEntityType
    fibo_properties: Dict[str, Any] = Field(default_factory=dict)
    mapping_confidence: float = 1.0
    created_at: datetime

    class Config:
        schema_extra = {
            "example": {
                "source_entity_id": "sec_aapl",
                "source_entity_type": "SECURITY",
                "fibo_entity_type": "EQUITY_INSTRUMENT",
                "fibo_properties": {
                    "instrument_name": "Apple Inc. Common Stock",
                    "shares_outstanding": 15728700000,
                },
                "mapping_confidence": 0.95,
            }
        }


class FIBOQuery(BaseModel):
    """Query model for FIBO ontology operations."""

    fibo_entity_types: Optional[List[FIBOEntityType]] = None
    fibo_relationship_types: Optional[List[FIBORelationshipType]] = None
    sparql_query: Optional[str] = None  # For advanced SPARQL queries
    include_mappings: bool = True
    limit: int = 100

    class Config:
        schema_extra = {
            "example": {
                "fibo_entity_types": ["EQUITY_INSTRUMENT", "POSITION_HOLDING"],
                "fibo_relationship_types": ["HAS_HOLDING"],
                "include_mappings": True,
                "limit": 50,
            }
        }
