from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""

    ACCOUNT = "Account"
    TRADE = "Trade"
    POSITION = "Position"
    SECURITY = "Security"
    COUNTERPARTY = "Counterparty"
    PORTFOLIO = "Portfolio"
    FUND = "Fund"
    CUSTODIAN = "Custodian"
    MARKET_DATA_PROVIDER = "MarketDataProvider"
    MCP_SERVER = "MCPServer"
    WORKFLOW = "Workflow"
    DATA_STREAM = "DataStream"
    DATA_FLOW = "DataFlow"
    RISK_MEASURE = "RiskMeasure"
    COMPLIANCE_RULE = "ComplianceRule"
    SETTLEMENT = "Settlement"
    CORPORATE_ACTION = "CorporateAction"


class RelationshipType(str, Enum):
    """Types of relationships in the knowledge graph."""

    HOLDS = "HOLDS"
    TRADES = "TRADES"
    SETTLES = "SETTLES"
    MANAGES = "MANAGES"
    PROVIDES_DATA = "PROVIDES_DATA"
    CONNECTS_TO = "CONNECTS_TO"
    EXECUTES = "EXECUTES"
    PROCESSES = "PROCESSES"
    VALIDATES = "VALIDATES"
    REPORTS_TO = "REPORTS_TO"
    INHERITS_FROM = "INHERITS_FROM"
    DEPENDS_ON = "DEPENDS_ON"
    AFFECTS = "AFFECTS"
    CONTAINS = "CONTAINS"
    REFERENCES = "REFERENCES"
    TRIGGERS = "TRIGGERS"
    MONITORS = "MONITORS"


class BaseEntity(BaseModel):
    """Base model for all knowledge graph entities."""

    id: str
    name: str
    description: Optional[str] = None
    entity_type: EntityType
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Account(BaseEntity):
    """Account entity representing client accounts."""

    entity_type: EntityType = EntityType.ACCOUNT
    account_number: str
    account_type: str  # e.g., "CUSTODY", "TRADING", "OMNIBUS"
    base_currency: str
    custodian_id: Optional[str] = None
    fund_id: Optional[str] = None
    status: str = "ACTIVE"

    class Config:
        schema_extra = {
            "example": {
                "id": "acc_12345",
                "name": "Global Equity Fund - USD",
                "account_number": "123456789",
                "account_type": "CUSTODY",
                "base_currency": "USD",
                "custodian_id": "state_street_001",
                "fund_id": "fund_gef_001",
                "status": "ACTIVE",
            }
        }


class Security(BaseEntity):
    """Security entity representing financial instruments."""

    entity_type: EntityType = EntityType.SECURITY
    symbol: str
    isin: Optional[str] = None
    cusip: Optional[str] = None
    sedol: Optional[str] = None
    security_type: str  # e.g., "EQUITY", "BOND", "DERIVATIVE"
    currency: str
    exchange: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "sec_aapl",
                "name": "Apple Inc.",
                "symbol": "AAPL",
                "isin": "US0378331005",
                "security_type": "EQUITY",
                "currency": "USD",
                "exchange": "NASDAQ",
                "sector": "Technology",
                "country": "US",
            }
        }


class Trade(BaseEntity):
    """Trade entity representing executed trades."""

    entity_type: EntityType = EntityType.TRADE
    trade_id: str
    account_id: str
    security_id: str
    trade_date: datetime
    settlement_date: datetime
    side: str  # "BUY" or "SELL"
    quantity: float
    price: float
    gross_amount: float
    net_amount: float
    commission: float
    fees: float
    currency: str
    counterparty_id: Optional[str] = None
    execution_venue: Optional[str] = None
    status: str = "EXECUTED"

    class Config:
        schema_extra = {
            "example": {
                "id": "trade_001",
                "name": "AAPL Purchase 1000 shares",
                "trade_id": "TRD123456",
                "account_id": "acc_12345",
                "security_id": "sec_aapl",
                "side": "BUY",
                "quantity": 1000,
                "price": 150.25,
                "gross_amount": 150250.00,
                "currency": "USD",
                "status": "EXECUTED",
            }
        }


class Position(BaseEntity):
    """Position entity representing holdings."""

    entity_type: EntityType = EntityType.POSITION
    account_id: str
    security_id: str
    quantity: float
    market_value: float
    book_cost: float
    unrealized_pnl: float
    currency: str
    as_of_date: datetime

    class Config:
        schema_extra = {
            "example": {
                "id": "pos_001",
                "name": "AAPL Position",
                "account_id": "acc_12345",
                "security_id": "sec_aapl",
                "quantity": 5000,
                "market_value": 752500.00,
                "book_cost": 750000.00,
                "unrealized_pnl": 2500.00,
                "currency": "USD",
            }
        }


class MCPServerEntity(BaseEntity):
    """MCP Server entity in the knowledge graph."""

    entity_type: EntityType = EntityType.MCP_SERVER
    server_url: str
    provider_type: str  # "CUSTODIAN", "MARKET_DATA", "PRICING"
    auth_type: str
    capabilities: List[str]
    status: str
    version: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "mcp_state_street",
                "name": "State Street MCP Server",
                "server_url": "https://api.statestreet.com/mcp",
                "provider_type": "CUSTODIAN",
                "auth_type": "API_KEY",
                "capabilities": ["positions", "trades", "cash_balances"],
                "status": "CONNECTED",
            }
        }


class WorkflowEntity(BaseEntity):
    """Workflow entity in the knowledge graph."""

    entity_type: EntityType = EntityType.WORKFLOW
    workflow_type: str
    status: str
    trigger_schedule: Optional[str] = None
    last_execution: Optional[datetime] = None
    success_rate: Optional[float] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "wf_daily_recon",
                "name": "Daily Position Reconciliation",
                "workflow_type": "DATA_RECONCILIATION",
                "status": "ACTIVE",
                "trigger_schedule": "0 18 * * 1-5",
                "success_rate": 99.5,
            }
        }


class DataStreamEntity(BaseEntity):
    """Data Stream entity in the knowledge graph."""

    entity_type: EntityType = EntityType.DATA_STREAM
    data_type: str
    source_system: str
    target_systems: List[str]
    status: str
    throughput_rps: Optional[float] = None
    latency_ms: Optional[float] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "stream_market_data",
                "name": "Real-time Market Data Stream",
                "data_type": "MARKET_PRICES",
                "source_system": "bloomberg_mcp",
                "target_systems": ["risk_system", "portfolio_management"],
                "status": "ACTIVE",
                "throughput_rps": 1500.0,
                "latency_ms": 45.0,
            }
        }


class BaseRelationship(BaseModel):
    """Base model for relationships."""

    relationship_type: RelationshipType
    from_entity_id: str
    to_entity_id: str
    created_at: datetime
    properties: Dict[str, Any] = Field(default_factory=dict)


class HoldsRelationship(BaseRelationship):
    """Relationship representing account holdings."""

    relationship_type: RelationshipType = RelationshipType.HOLDS
    quantity: float
    market_value: float
    percentage: Optional[float] = None
    as_of_date: datetime


class TradesRelationship(BaseRelationship):
    """Relationship representing trading activity."""

    relationship_type: RelationshipType = RelationshipType.TRADES
    trade_count: int
    total_volume: float
    last_trade_date: datetime


class ProvidesDataRelationship(BaseRelationship):
    """Relationship representing data provision."""

    relationship_type: RelationshipType = RelationshipType.PROVIDES_DATA
    data_types: List[str]
    frequency: str  # "REAL_TIME", "DAILY", "INTRADAY"
    quality_score: Optional[float] = None


class ExecutesRelationship(BaseRelationship):
    """Relationship representing workflow execution."""

    relationship_type: RelationshipType = RelationshipType.EXECUTES
    execution_count: int
    success_count: int
    avg_duration_ms: float
    last_execution: datetime


class KnowledgeGraphQuery(BaseModel):
    """Query model for knowledge graph operations."""

    entity_types: Optional[List[EntityType]] = None
    relationship_types: Optional[List[RelationshipType]] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    depth: int = 1
    limit: int = 100
    include_relationships: bool = True


class GraphTraversal(BaseModel):
    """Model for graph traversal operations."""

    start_entity_id: str
    traversal_pattern: str  # Cypher pattern like "(n)-[r]->(m)"
    max_depth: int = 3
    filters: Dict[str, Any] = Field(default_factory=dict)
    return_paths: bool = False


class GraphAnalytics(BaseModel):
    """Model for graph analytics results."""

    centrality_measures: Dict[str, float] = Field(default_factory=dict)
    clustering_coefficient: Optional[float] = None
    connected_components: List[List[str]] = Field(default_factory=list)
    shortest_paths: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    community_detection: Dict[str, str] = Field(default_factory=dict)


class GraphVisualization(BaseModel):
    """Model for graph visualization data."""

    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    layout: str = "force"  # "force", "hierarchical", "circular"
    filters: Dict[str, Any] = Field(default_factory=dict)
    zoom_level: float = 1.0
    center_node: Optional[str] = None
