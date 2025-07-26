from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text
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
    category = Column(
        String, nullable=False, index=True
    )  # e.g., "Trade Settlement", "Reconciliation"
    subcategory = Column(String, index=True)
    process_type = Column(
        String, index=True
    )  # e.g., "Manual", "Semi-Automated", "Automated"
    business_area = Column(
        String, index=True
    )  # e.g., "Custody", "Securities Lending", "FX"

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
