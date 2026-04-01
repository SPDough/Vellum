from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

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
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REQUIRES_HUMAN_INTERVENTION = "REQUIRES_HUMAN_INTERVENTION"


class WorkflowType(str, Enum):
    """Types of automated workflows."""

    TRADE_VALIDATION = "TRADE_VALIDATION"
    SETTLEMENT_PROCESSING = "SETTLEMENT_PROCESSING"
    RECONCILIATION = "RECONCILIATION"
    EXCEPTION_HANDLING = "EXCEPTION_HANDLING"
    REGULATORY_REPORTING = "REGULATORY_REPORTING"
    CLIENT_ONBOARDING = "CLIENT_ONBOARDING"
    CORPORATE_ACTIONS = "CORPORATE_ACTIONS"


class NodeType(str, Enum):
    """LangGraph node types."""

    START = "START"
    END = "END"
    DECISION = "DECISION"
    ACTION = "ACTION"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    LLM_CALL = "LLM_CALL"
    RULES_ENGINE = "RULES_ENGINE"
    DATA_RETRIEVAL = "DATA_RETRIEVAL"
    API_CALL = "API_CALL"


class WorkflowNode(Base):
    """Individual workflow node definition."""

    __tablename__ = "workflow_nodes"

    id = Column(String, primary_key=True)
    workflow_definition_id = Column(
        String, ForeignKey("workflow_definitions.id"), nullable=False, index=True
    )
    node_id = Column(String, nullable=False)
    node_type = Column(String, nullable=False)
    node_name = Column(String, nullable=False)
    node_config = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# SQLAlchemy Models
class WorkflowDefinition(Base):
    """Definition of automated workflows based on SOPs."""

    __tablename__ = "workflow_definitions"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    workflow_type = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)

    # Source SOP
    base_sop_id = Column(String, index=True)  # SOP this workflow implements

    # Graph definition (LangGraph structure)
    graph_definition = Column(JSON, nullable=False)  # Serialized LangGraph

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)

    # Status
    is_active = Column(Boolean, default=True)
    is_tested = Column(Boolean, default=False)
    test_success_rate = Column(Float)

    # Performance metrics
    average_execution_time = Column(Integer)  # seconds
    success_rate = Column(Float)  # percentage
    human_intervention_rate = Column(Float)  # percentage

    # Relationships
    executions = relationship("WorkflowExecution", back_populates="definition")


class WorkflowExecution(Base):
    """Individual workflow execution instances."""

    __tablename__ = "workflow_executions"

    id = Column(String, primary_key=True)
    workflow_definition_id = Column(
        String, ForeignKey("workflow_definitions.id"), nullable=False, index=True
    )

    # Execution context
    trigger_type = Column(
        String, nullable=False
    )  # "TRADE_EVENT", "SCHEDULED", "MANUAL"
    trigger_data = Column(JSON)  # Data that triggered the workflow

    # Status
    status = Column(String, default=WorkflowStatus.PENDING, index=True)
    current_node = Column(String)  # Current step in the workflow

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Results
    result_data = Column(JSON)
    error_message = Column(Text)
    requires_human_review = Column(Boolean, default=False)
    human_review_reason = Column(Text)

    # Temporal workflow ID for correlation
    temporal_workflow_id = Column(String, index=True)

    # Relationships
    definition = relationship("WorkflowDefinition", back_populates="executions")
    node_executions = relationship("NodeExecution", back_populates="workflow_execution")


class NodeExecution(Base):
    """Individual node execution within a workflow."""

    __tablename__ = "node_executions"

    id = Column(String, primary_key=True)
    workflow_execution_id = Column(
        String, ForeignKey("workflow_executions.id"), nullable=False, index=True
    )

    node_id = Column(String, nullable=False)
    node_type = Column(String, nullable=False)
    node_name = Column(String, nullable=False)

    # Execution details
    status = Column(
        String, nullable=False
    )  # PENDING, RUNNING, COMPLETED, FAILED, SKIPPED
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Input/Output
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)

    # LLM specific data
    llm_model = Column(String)
    llm_tokens_used = Column(Integer)
    llm_cost = Column(Float)
    prompt_template = Column(String)

    # Human intervention
    requires_human_input = Column(Boolean, default=False)
    human_input_received = Column(JSON)
    assigned_to = Column(String)

    # Relationships
    workflow_execution = relationship(
        "WorkflowExecution", back_populates="node_executions"
    )


# Pydantic Models
class WorkflowDefinitionBase(BaseModel):
    """Base workflow definition model."""

    name: str
    description: Optional[str] = None
    workflow_type: WorkflowType
    version: str
    base_sop_id: Optional[str] = None
    graph_definition: Dict[str, Any]


class WorkflowDefinitionCreate(WorkflowDefinitionBase):
    """Model for creating workflow definitions."""

    created_by: str


class WorkflowDefinitionResponse(WorkflowDefinitionBase):
    """Workflow definition response model."""

    id: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    is_active: bool
    is_tested: bool
    test_success_rate: Optional[float] = None
    average_execution_time: Optional[int] = None
    success_rate: Optional[float] = None
    human_intervention_rate: Optional[float] = None

    class Config:
        from_attributes = True


class WorkflowExecutionCreate(BaseModel):
    """Model for creating workflow executions."""

    workflow_definition_id: str
    trigger_type: str
    trigger_data: Dict[str, Any]


class WorkflowExecutionResponse(BaseModel):
    """Workflow execution response model."""

    id: str
    workflow_definition_id: str
    trigger_type: str
    status: WorkflowStatus
    current_node: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    requires_human_review: bool
    human_review_reason: Optional[str] = None
    temporal_workflow_id: Optional[str] = None

    class Config:
        from_attributes = True


class NodeExecutionResponse(BaseModel):
    """Node execution response model."""

    id: str
    workflow_execution_id: str
    node_id: str
    node_type: NodeType
    node_name: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    requires_human_input: bool
    assigned_to: Optional[str] = None
    llm_model: Optional[str] = None
    llm_tokens_used: Optional[int] = None
    llm_cost: Optional[float] = None

    class Config:
        from_attributes = True


class HumanReviewRequest(BaseModel):
    """Request for human review during workflow execution."""

    workflow_execution_id: str
    node_execution_id: str
    review_type: str
    context: Dict[str, Any]
    urgency: str  # LOW, MEDIUM, HIGH, CRITICAL
    assigned_to: Optional[str] = None
    deadline: Optional[datetime] = None


class HumanReviewResponse(BaseModel):
    """Human review response."""

    decision: str  # APPROVE, REJECT, MODIFY, ESCALATE
    comments: str
    modified_data: Optional[Dict[str, Any]] = None
    escalate_to: Optional[str] = None


class WorkflowMetrics(BaseModel):
    """Workflow performance metrics."""

    workflow_definition_id: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_duration_seconds: float
    success_rate: float
    human_intervention_rate: float
    total_cost: float
    total_tokens_used: int
    most_common_failure_reasons: List[Dict[str, Any]]


class AutomationInsight(BaseModel):
    """Insights about automation opportunities."""

    sop_id: str
    current_manual_steps: int
    automatable_steps: int
    automation_potential: float  # percentage
    estimated_time_savings: int  # minutes per execution
    estimated_cost_savings: float  # USD per execution
    implementation_complexity: str  # LOW, MEDIUM, HIGH
    recommended_approach: str
    risks: List[str]
    prerequisites: List[str]
