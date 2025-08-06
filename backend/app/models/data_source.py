from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class DataSourceType(str, Enum):
    """Types of data sources for scheduled data pulls."""

    API = "API"
    MCP_SERVER = "MCP_SERVER"
    WEB_SCRAPING = "WEB_SCRAPING"
    DATABASE = "DATABASE"
    FILE_UPLOAD = "FILE_UPLOAD"


class ScheduleType(str, Enum):
    """Types of scheduling for data pulls."""

    MANUAL = "MANUAL"
    INTERVAL = "INTERVAL"  # Every X minutes/hours/days
    CRON = "CRON"  # Cron expression
    EVENT_DRIVEN = "EVENT_DRIVEN"  # Triggered by events


class DataPullStatus(str, Enum):
    """Status of data pull executions."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SCHEDULED = "SCHEDULED"


# SQLAlchemy Models
class DataSourceConfiguration(Base):
    """Configuration for scheduled data pull workflows."""

    __tablename__ = "data_source_configurations"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    data_source_type = Column(String, nullable=False, index=True)

    # Source-specific configuration
    source_config = Column(JSON, nullable=False)  # URL, headers, auth, etc.

    # Data processing configuration
    processing_config = Column(JSON)  # Pandas operations, transformations

    # Schedule configuration
    schedule_type = Column(String, nullable=False, default=ScheduleType.MANUAL)
    schedule_config = Column(JSON)  # Cron expression, interval, etc.

    # Output configuration
    output_to_sandbox = Column(Boolean, default=True)
    output_table_name = Column(String)  # Table name in data sandbox

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)

    # Status
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)

    # Performance metrics
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    avg_execution_time_seconds = Column(Integer)

    # Relationships
    executions = relationship("DataPullExecution", back_populates="configuration")


class DataPullExecution(Base):
    """Individual execution of a data pull workflow."""

    __tablename__ = "data_pull_executions"

    id = Column(String, primary_key=True)
    configuration_id = Column(
        String, ForeignKey("data_source_configurations.id"), nullable=False, index=True
    )

    # Execution details
    status = Column(String, default=DataPullStatus.PENDING, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Data details
    records_processed = Column(Integer)
    records_successful = Column(Integer)
    records_failed = Column(Integer)
    data_size_bytes = Column(Integer)

    # Results
    output_location = Column(String)  # Where the data was stored
    error_message = Column(Text)
    execution_log = Column(JSON)  # Detailed execution log

    # Triggered by
    trigger_type = Column(String)  # SCHEDULED, MANUAL, EVENT
    triggered_by = Column(String)  # User ID or system

    # Relationships
    configuration = relationship("DataSourceConfiguration", back_populates="executions")


# Pydantic Models
class DataSourceConfigurationBase(BaseModel):
    """Base data source configuration model."""

    name: str
    description: Optional[str] = None
    data_source_type: DataSourceType
    source_config: Dict[str, Any]
    processing_config: Optional[Dict[str, Any]] = None
    schedule_type: ScheduleType = ScheduleType.MANUAL
    schedule_config: Optional[Dict[str, Any]] = None
    output_to_sandbox: bool = True
    output_table_name: Optional[str] = None


class DataSourceConfigurationCreate(DataSourceConfigurationBase):
    """Model for creating data source configurations."""

    created_by: str


class DataSourceConfigurationUpdate(BaseModel):
    """Model for updating data source configurations."""

    name: Optional[str] = None
    description: Optional[str] = None
    source_config: Optional[Dict[str, Any]] = None
    processing_config: Optional[Dict[str, Any]] = None
    schedule_type: Optional[ScheduleType] = None
    schedule_config: Optional[Dict[str, Any]] = None
    output_to_sandbox: Optional[bool] = None
    output_table_name: Optional[str] = None
    is_active: Optional[bool] = None


class DataSourceConfigurationResponse(DataSourceConfigurationBase):
    """Data source configuration response model."""

    id: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    is_active: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    total_runs: int
    successful_runs: int
    failed_runs: int
    avg_execution_time_seconds: Optional[int] = None

    class Config:
        from_attributes = True


class DataPullExecutionCreate(BaseModel):
    """Model for creating data pull executions."""

    configuration_id: str
    trigger_type: str
    triggered_by: str


class DataPullExecutionResponse(BaseModel):
    """Data pull execution response model."""

    id: str
    configuration_id: str
    status: DataPullStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    records_processed: Optional[int] = None
    records_successful: Optional[int] = None
    records_failed: Optional[int] = None
    data_size_bytes: Optional[int] = None
    output_location: Optional[str] = None
    error_message: Optional[str] = None
    trigger_type: str
    triggered_by: str

    class Config:
        from_attributes = True


# Configuration Templates
class APISourceConfig(BaseModel):
    """Configuration for API data sources."""

    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, str]] = None
    auth_type: Optional[str] = None  # "bearer", "basic", "api_key", "oauth2"
    auth_config: Optional[Dict[str, str]] = None
    timeout_seconds: int = 30
    retry_attempts: int = 3
    response_format: str = "json"  # "json", "csv", "xml"


class MCPServerConfig(BaseModel):
    """Configuration for MCP Server data sources."""

    server_name: str
    tool_name: str
    tool_arguments: Optional[Dict[str, Any]] = None
    timeout_seconds: int = 60
    retry_attempts: int = 3


class WebScrapingConfig(BaseModel):
    """Configuration for web scraping data sources."""

    url: str
    selector_config: Dict[str, str]  # CSS selectors for data extraction
    browser_config: Optional[Dict[str, Any]] = None  # Playwright options
    wait_config: Optional[Dict[str, Any]] = None  # Wait conditions
    headers: Optional[Dict[str, str]] = None
    cookies: Optional[List[Dict[str, str]]] = None
    javascript_enabled: bool = True
    timeout_seconds: int = 60


class ProcessingConfig(BaseModel):
    """Configuration for data processing with Pandas."""

    data_cleaning: Optional[Dict[str, Any]] = None  # Drop duplicates, fill nulls
    transformations: Optional[List[Dict[str, Any]]] = None  # Column operations
    filters: Optional[List[Dict[str, Any]]] = None  # Row filtering
    aggregations: Optional[List[Dict[str, Any]]] = None  # Group by operations
    joins: Optional[List[Dict[str, Any]]] = None  # Join with other data sources


class ScheduleConfig(BaseModel):
    """Configuration for scheduling data pulls."""

    # For INTERVAL scheduling
    interval_seconds: Optional[int] = None
    interval_minutes: Optional[int] = None
    interval_hours: Optional[int] = None
    interval_days: Optional[int] = None

    # For CRON scheduling
    cron_expression: Optional[str] = None
    timezone: Optional[str] = "UTC"

    # For EVENT_DRIVEN scheduling
    event_source: Optional[str] = None
    event_filter: Optional[Dict[str, Any]] = None

    # General settings
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_runs: Optional[int] = None


class DataSourceTestRequest(BaseModel):
    """Request model for testing data source configurations."""

    data_source_type: DataSourceType
    source_config: Dict[str, Any]
    processing_config: Optional[Dict[str, Any]] = None
    sample_size: int = 10


class DataSourceTestResponse(BaseModel):
    """Response model for data source testing."""

    success: bool
    sample_data: Optional[List[Dict[str, Any]]] = None
    record_count: Optional[int] = None
    error_message: Optional[str] = None
    execution_time_seconds: Optional[float] = None
    data_schema: Optional[Dict[str, str]] = None  # Column name -> data type
