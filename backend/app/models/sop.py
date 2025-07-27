from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, JSON, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SOPDocument(Base):
    """Standard Operating Procedure document stored in both SQL and Neo4j."""
    __tablename__ = "sop_documents"
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False, index=True)
    document_number = Column(String, unique=True, nullable=False, index=True)
    version = Column(String, nullable=False)
    
    # Content
    content = Column(Text, nullable=False)
    summary = Column(Text)
    
    # Classification
    category = Column(String, nullable=False, index=True)  # e.g., "Trade Settlement", "Reconciliation"
    subcategory = Column(String, index=True)
    process_type = Column(String, index=True)  # e.g., "Manual", "Semi-Automated", "Automated"
    business_area = Column(String, index=True)  # e.g., "Custody", "Securities Lending", "FX"
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)
    last_reviewed = Column(DateTime)
    review_frequency_days = Column(Integer, default=365)
    
    # Status
    status = Column(String, default="ACTIVE")  # ACTIVE, DEPRECATED, UNDER_REVIEW
    is_automated = Column(Boolean, default=False)
    automation_percentage = Column(Float, default=0.0)  # 0-100%
    
    # Vector embeddings (stored as JSON for now)
    embeddings = Column(JSON)
    
    # Neo4j node ID for cross-reference
    neo4j_node_id = Column(String, index=True)


class SOPStep(Base):
    """Individual steps within an SOP document."""
    __tablename__ = "sop_steps"
    
    id = Column(String, primary_key=True)
    sop_document_id = Column(String, nullable=False, index=True)
    
    step_number = Column(Integer, nullable=False)
    step_title = Column(String, nullable=False)
    step_description = Column(Text, nullable=False)
    
    # Step metadata
    is_manual = Column(Boolean, default=True)
    is_automated = Column(Boolean, default=False)
    is_decision_point = Column(Boolean, default=False)
    estimated_duration_minutes = Column(Integer)
    
    # Automation details
    automation_tool = Column(String)  # e.g., "LangGraph", "Drools", "Custom Script"
    automation_confidence = Column(Float)  # 0-100%
    
    # Dependencies
    depends_on_steps = Column(JSON)  # List of step IDs this depends on
    prerequisite_data = Column(JSON)  # Required data/documents
    
    # Neo4j relationship IDs
    neo4j_relationships = Column(JSON)


# Pydantic Models
class SOPDocumentBase(BaseModel):
    """Base SOP document model."""
    title: str
    document_number: str
    version: str
    content: str
    summary: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    process_type: str
    business_area: str


class SOPDocumentCreate(SOPDocumentBase):
    """Model for creating SOP documents."""
    created_by: str


class SOPDocumentUpdate(BaseModel):
    """Model for updating SOP documents."""
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    process_type: Optional[str] = None
    status: Optional[str] = None
    is_automated: Optional[bool] = None
    automation_percentage: Optional[float] = None


class SOPDocumentResponse(SOPDocumentBase):
    """SOP document response model."""
    id: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    last_reviewed: Optional[datetime] = None
    status: str
    is_automated: bool
    automation_percentage: float
    neo4j_node_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class SOPStepBase(BaseModel):
    """Base SOP step model."""
    step_number: int
    step_title: str
    step_description: str
    is_manual: bool = True
    is_automated: bool = False
    is_decision_point: bool = False
    estimated_duration_minutes: Optional[int] = None


class SOPStepCreate(SOPStepBase):
    """Model for creating SOP steps."""
    sop_document_id: str


class SOPStepResponse(SOPStepBase):
    """SOP step response model."""
    id: str
    sop_document_id: str
    automation_tool: Optional[str] = None
    automation_confidence: Optional[float] = None
    depends_on_steps: Optional[List[str]] = None
    prerequisite_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class SOPSearchRequest(BaseModel):
    """Model for searching SOP documents."""
    query: str
    category: Optional[str] = None
    business_area: Optional[str] = None
    process_type: Optional[str] = None
    include_automated: bool = True
    include_manual: bool = True
    limit: int = Field(default=20, le=100)


class SOPSearchResult(BaseModel):
    """SOP search result."""
    id: str
    title: str
    document_number: str
    category: str
    business_area: str
    summary: Optional[str] = None
    relevance_score: float
    automation_percentage: float
    
    class Config:
        from_attributes = True


class SOPRecommendation(BaseModel):
    """SOP recommendation for a specific trade or process."""
    sop_id: str
    title: str
    relevance_score: float
    confidence: float
    reasoning: str
    applicable_steps: List[str]
    estimated_automation_time_savings: Optional[int] = None  # minutes


class ProcessAutomationSuggestion(BaseModel):
    """Suggestion for automating a manual process."""
    sop_id: str
    step_ids: List[str]
    automation_approach: str  # "LangGraph", "Rules Engine", "RPA", etc.
    confidence: float
    expected_success_rate: float
    implementation_effort: str  # "LOW", "MEDIUM", "HIGH"
    risk_assessment: str
    prerequisites: List[str]


# Enhanced SOP Execution Models

class SOPExecutionStatus(str):
    """Status of SOP Execution"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REQUIRES_APPROVAL = "requires_approval"


class SOPStepExecutionStatus(str):
    """Status of individual SOP step execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    REQUIRES_APPROVAL = "requires_approval"


class SOPExecution(Base):
    """SOP execution tracking table"""
    __tablename__ = "sop_executions"
    
    id = Column(String, primary_key=True)
    sop_document_id = Column(String, nullable=False, index=True)
    execution_name = Column(String, nullable=False)
    status = Column(String, default=SOPExecutionStatus.NOT_STARTED)
    
    # Execution metadata
    initiated_by = Column(String, nullable=False)
    assigned_to = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    estimated_duration_minutes = Column(Integer)
    actual_duration_minutes = Column(Integer)
    
    # Context and data
    context_data = Column(JSON)  # Trade data, client info, etc.
    input_parameters = Column(JSON)
    final_output = Column(JSON)
    
    # Progress tracking
    current_step_id = Column(String)
    completed_steps = Column(JSON)  # List of completed step IDs
    failed_steps = Column(JSON)  # List of failed step IDs
    
    # Compliance and approval
    requires_approval = Column(Boolean, default=False)
    approval_status = Column(String)  # PENDING, APPROVED, REJECTED
    approval_notes = Column(Text)
    approved_by = Column(String)
    approved_at = Column(DateTime)
    
    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    execution_log = Column(JSON)  # Detailed log of execution events


class SOPStepExecution(Base):
    """Individual step execution tracking"""
    __tablename__ = "sop_step_executions"
    
    id = Column(String, primary_key=True)
    sop_execution_id = Column(String, nullable=False, index=True)
    step_id = Column(String, nullable=False)
    status = Column(String, default=SOPStepExecutionStatus.PENDING)
    
    # Execution details
    started_by = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    actual_duration_minutes = Column(Integer)
    
    # Step results
    input_data = Column(JSON)
    output_data = Column(JSON)
    validation_results = Column(JSON)
    automation_results = Column(JSON)
    
    # Notes and documentation
    execution_notes = Column(Text)
    documents_generated = Column(JSON)  # List of generated document paths
    approval_details = Column(JSON)
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic models for SOP execution

class SOPExecutionCreate(BaseModel):
    """Model for creating SOP execution"""
    sop_document_id: str
    execution_name: str
    initiated_by: str
    assigned_to: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    input_parameters: Optional[Dict[str, Any]] = None


class SOPExecutionUpdate(BaseModel):
    """Model for updating SOP execution"""
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    current_step_id: Optional[str] = None
    approval_status: Optional[str] = None
    approval_notes: Optional[str] = None


class SOPExecutionResponse(BaseModel):
    """SOP execution response model"""
    id: str
    sop_document_id: str
    execution_name: str
    status: str
    initiated_by: str
    assigned_to: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_duration_minutes: Optional[int] = None
    actual_duration_minutes: Optional[int] = None
    current_step_id: Optional[str] = None
    completion_percentage: Optional[float] = None
    requires_approval: bool
    approval_status: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SOPStepExecutionCreate(BaseModel):
    """Model for creating step execution"""
    sop_execution_id: str
    step_id: str
    started_by: str
    input_data: Optional[Dict[str, Any]] = None


class SOPStepExecutionUpdate(BaseModel):
    """Model for updating step execution"""
    status: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    validation_results: Optional[Dict[str, Any]] = None
    execution_notes: Optional[str] = None
    error_message: Optional[str] = None


class SOPStepExecutionResponse(BaseModel):
    """Step execution response model"""
    id: str
    sop_execution_id: str
    step_id: str
    status: str
    started_by: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    actual_duration_minutes: Optional[int] = None
    execution_notes: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class SOPExecutionSummary(BaseModel):
    """Summary of SOP execution with key metrics"""
    execution_id: str
    sop_title: str
    status: str
    total_steps: int
    completed_steps: int
    failed_steps: int
    progress_percentage: float
    estimated_time_remaining_minutes: Optional[int] = None
    compliance_status: str
    risk_alerts: List[str] = []


class SOPTemplateLibrary:
    """Library of pre-defined SOP templates for custodian banking"""
    
    @staticmethod
    def get_trade_settlement_template() -> Dict[str, Any]:
        """Trade Settlement SOP Template"""
        return {
            "title": "Equity Trade Settlement Procedure",
            "document_number": "SOP-TS-001",
            "version": "1.0",
            "category": "Trade Settlement",
            "business_area": "Custody Operations", 
            "process_type": "Semi-Automated",
            "content": """
# Equity Trade Settlement Procedure

## Purpose
This procedure defines the complete process for settling equity trades in compliance with regulatory requirements and internal controls.

## Scope
Applies to all equity trades processed through the custodian platform.

## Procedure Steps
1. Trade Validation
2. Confirmation Generation
3. Settlement Instructions
4. Final Settlement Monitoring
            """,
            "summary": "Complete procedure for equity trade settlement including validation, confirmation, and monitoring",
            "steps": [
                {
                    "step_number": 1,
                    "step_title": "Trade Validation",
                    "step_description": "Validate trade details against market data and client limits",
                    "is_automated": True,
                    "estimated_duration_minutes": 5,
                    "automation_tool": "Rules Engine"
                },
                {
                    "step_number": 2,
                    "step_title": "Generate Trade Confirmation",
                    "step_description": "Generate and send trade confirmation to counterparty",
                    "is_automated": True,
                    "estimated_duration_minutes": 10,
                    "automation_tool": "LangGraph"
                },
                {
                    "step_number": 3,
                    "step_title": "Settlement Instructions",
                    "step_description": "Prepare and send settlement instructions",
                    "is_manual": True,
                    "estimated_duration_minutes": 15,
                    "is_decision_point": True
                },
                {
                    "step_number": 4,
                    "step_title": "Final Settlement",
                    "step_description": "Monitor and confirm settlement completion",
                    "is_automated": True,
                    "estimated_duration_minutes": 30,
                    "automation_tool": "Monitoring System"
                }
            ]
        }
    
    @staticmethod
    def get_corporate_actions_template() -> Dict[str, Any]:
        """Corporate Actions SOP Template"""
        return {
            "title": "Corporate Actions Processing",
            "document_number": "SOP-CA-001", 
            "version": "1.0",
            "category": "Corporate Actions",
            "business_area": "Asset Servicing",
            "process_type": "Semi-Automated",
            "content": """
# Corporate Actions Processing Procedure

## Purpose
Process corporate actions including dividends, stock splits, and rights issues.

## Scope
All corporate actions affecting client holdings.

## Procedure Steps
1. Corporate Action Notification
2. Client Notification 
3. Election Processing
4. Entitlement Calculation
            """,
            "summary": "Complete corporate actions processing including notifications and entitlements",
            "steps": [
                {
                    "step_number": 1,
                    "step_title": "Corporate Action Notification",
                    "step_description": "Receive and validate corporate action announcement",
                    "is_automated": True,
                    "estimated_duration_minutes": 5
                },
                {
                    "step_number": 2,
                    "step_title": "Client Notification",
                    "step_description": "Notify affected clients of corporate action",
                    "is_automated": True,
                    "estimated_duration_minutes": 15
                },
                {
                    "step_number": 3,
                    "step_title": "Process Client Elections",
                    "step_description": "Process client elections and instructions",
                    "is_manual": True,
                    "estimated_duration_minutes": 45,
                    "is_decision_point": True
                },
                {
                    "step_number": 4,
                    "step_title": "Calculate Entitlements",
                    "step_description": "Calculate client entitlements and process payments",
                    "is_automated": True,
                    "estimated_duration_minutes": 20
                }
            ]
        }

    @staticmethod
    def get_all_templates() -> Dict[str, Dict[str, Any]]:
        """Get all available SOP templates"""
        return {
            "TRADE_SETTLEMENT": SOPTemplateLibrary.get_trade_settlement_template(),
            "CORPORATE_ACTIONS": SOPTemplateLibrary.get_corporate_actions_template()
        }