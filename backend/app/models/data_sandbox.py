import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


from app.models.workflow import Base


class DataSourceType(str, Enum):
    WORKFLOW = "workflow"
    MCP = "mcp"
    AGENT = "agent"
    API = "api"
    MANUAL = "manual"


class DataSourceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class DataFieldType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    OBJECT = "object"
    ARRAY = "array"


class FilterOperator(str, Enum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NIN = "nin"
    LIKE = "like"
    REGEX = "regex"


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # DataSourceType
    description = Column(Text)
    schema = Column(JSON)  # DataSchema
    status = Column(String, nullable=False, default=DataSourceStatus.ACTIVE)
    record_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Source-specific metadata
    source_metadata = Column(JSON)  # workflow_id, mcp_server_id, etc.

    # Configuration
    config = Column(JSON)  # refresh_interval, retention_policy, etc.

    # Relationships
    data_records = relationship(
        "DataRecord", back_populates="data_source", cascade="all, delete-orphan"
    )
    transformations = relationship(
        "DataTransformation", back_populates="source_data_source"
    )


class DataRecord(Base):
    __tablename__ = "data_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    data_source_id = Column(String, ForeignKey("data_sources.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    data = Column(JSON, nullable=False)
    metadata = Column(JSON)  # execution_id, step_name, etc.

    # Relationships
    data_source = relationship("DataSource", back_populates="data_records")


class DataTransformation(Base):
    __tablename__ = "data_transformations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    source_data_source_id = Column(
        String, ForeignKey("data_sources.id"), nullable=False
    )
    transformations = Column(JSON, nullable=False)  # Array of transformation steps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    source_data_source = relationship("DataSource")


class DataVisualization(Base):
    __tablename__ = "data_visualizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text)
    type = Column(String, nullable=False)  # table, chart, graph, map
    config = Column(JSON, nullable=False)
    created_by = Column(String)  # user_id
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SharedDataView(Base):
    __tablename__ = "shared_data_views"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    share_id = Column(
        String, unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    query = Column(JSON, nullable=False)
    visualization = Column(JSON)
    permissions = Column(JSON, nullable=False)
    expires_at = Column(DateTime)
    created_by = Column(String)  # user_id
    created_at = Column(DateTime, default=datetime.utcnow)


# Pydantic Models
class DataField(BaseModel):
    name: str
    type: DataFieldType
    required: bool = False
    description: Optional[str] = None
    format: Optional[str] = None


class DataSchema(BaseModel):
    fields: List[DataField]


class DataFilter(BaseModel):
    field: str
    operator: FilterOperator
    value: Any


class DataSort(BaseModel):
    field: str
    direction: str = Field(..., pattern="^(asc|desc)$")


class DataQuery(BaseModel):
    source: str
    filters: Optional[List[DataFilter]] = None
    sorts: Optional[List[DataSort]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    fields: Optional[List[str]] = None


class DataSourceCreate(BaseModel):
    name: str
    type: DataSourceType
    description: Optional[str] = None
    data_schema: Optional[DataSchema] = Field(None, alias="schema")
    source_metadata: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None


class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[DataSourceStatus] = None
    data_schema: Optional[DataSchema] = Field(None, alias="schema")
    config: Optional[Dict[str, Any]] = None


class DataSourceResponse(BaseModel):
    id: str
    name: str
    type: DataSourceType
    description: Optional[str]
    data_schema: Optional[DataSchema] = Field(None, alias="schema")
    status: DataSourceStatus
    record_count: int
    last_updated: datetime
    created_at: datetime
    source_metadata: Optional[Dict[str, Any]]
    config: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class DataQueryResult(BaseModel):
    data: List[Dict[str, Any]]
    total_count: int
    data_schema: Optional[DataSchema] = Field(None, alias="schema")
    execution_time: float
    source: DataSourceResponse


class WorkflowOutputCreate(BaseModel):
    workflow_id: str
    workflow_name: str
    execution_id: str
    step_name: str
    data: Any
    data_schema: Optional[DataSchema] = Field(None, alias="schema")
    metadata: Dict[str, Any]


class WorkflowOutput(BaseModel):
    id: str
    workflow_id: str
    workflow_name: str
    execution_id: str
    step_name: str
    data: Any
    data_schema: Optional[DataSchema] = Field(None, alias="schema")
    timestamp: datetime
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class MCPDataStreamCreate(BaseModel):
    server_id: str
    server_name: str
    stream_name: str
    data: Any
    data_schema: Optional[DataSchema] = Field(None, alias="schema")
    metadata: Dict[str, Any]


class MCPDataStream(BaseModel):
    id: str
    server_id: str
    server_name: str
    stream_name: str
    data: Any
    data_schema: Optional[DataSchema] = Field(None, alias="schema")
    timestamp: datetime
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class AgentResultCreate(BaseModel):
    agent_id: str
    agent_name: str
    execution_id: str
    task_type: str
    result: Any
    data_schema: Optional[DataSchema] = Field(None, alias="schema")
    metadata: Dict[str, Any]


class AgentResult(BaseModel):
    id: str
    agent_id: str
    agent_name: str
    execution_id: str
    task_type: str
    result: Any
    data_schema: Optional[DataSchema] = Field(None, alias="schema")
    timestamp: datetime
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class DataExportRequest(BaseModel):
    query: DataQuery
    format: str = Field(..., pattern="^(csv|json|xlsx|parquet)$")
    filename: Optional[str] = None


class DataVisualizationConfig(BaseModel):
    type: str = Field(..., pattern="^(table|chart|graph|map)$")
    title: str
    description: Optional[str] = None
    config: Dict[str, Any]


class DataVisualizationCreate(BaseModel):
    title: str
    description: Optional[str] = None
    type: str = Field(..., pattern="^(table|chart|graph|map)$")
    config: Dict[str, Any]


class DataVisualizationResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    type: str
    config: Dict[str, Any]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DataQualityAnalysis(BaseModel):
    completeness: float
    accuracy: float
    consistency: float
    timeliness: float
    issues: List[Dict[str, Any]]


class DataLineage(BaseModel):
    upstream: List[Dict[str, Any]]
    downstream: List[Dict[str, Any]]
