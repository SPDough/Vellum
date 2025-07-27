from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class TradeStatus(str, Enum):
    """Trade processing status enumeration."""

    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    MATCHED = "MATCHED"
    CONFIRMED = "CONFIRMED"
    SETTLED = "SETTLED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REQUIRES_MANUAL_REVIEW = "REQUIRES_MANUAL_REVIEW"


class TradeType(str, Enum):
    """Trade type enumeration."""

    EQUITY = "EQUITY"
    BOND = "BOND"
    FX = "FX"
    DERIVATIVE = "DERIVATIVE"
    REPO = "REPO"
    SECURITIES_LENDING = "SECURITIES_LENDING"


class Priority(str, Enum):
    """Processing priority levels."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


# SQLAlchemy Models
class Trade(Base):
    """Core trade entity for post-trade processing."""

    __tablename__ = "trades"

    id = Column(String, primary_key=True)
    trade_reference = Column(String, unique=True, nullable=False, index=True)
    counterparty_id = Column(String, nullable=False, index=True)
    instrument_id = Column(String, nullable=False, index=True)

    # Trade details
    trade_type = Column(String, nullable=False)
    side = Column(String, nullable=False)  # BUY/SELL
    quantity = Column(Numeric(precision=18, scale=8), nullable=False)
    price = Column(Numeric(precision=18, scale=8), nullable=False)
    trade_value = Column(Numeric(precision=18, scale=2), nullable=False)
    currency = Column(String(3), nullable=False)

    # Dates
    trade_date = Column(DateTime, nullable=False)
    settlement_date = Column(DateTime, nullable=False)
    value_date = Column(DateTime)

    # Processing status
    status = Column(String, default=TradeStatus.PENDING, index=True)
    priority = Column(String, default=Priority.NORMAL)
    requires_manual_review = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_by = Column(String)
    notes = Column(Text)

    # Relationships
    exceptions = relationship("TradeException", back_populates="trade")
    processing_steps = relationship("ProcessingStep", back_populates="trade")


class TradeException(Base):
    """Trade processing exceptions requiring manual intervention."""

    __tablename__ = "trade_exceptions"

    id = Column(String, primary_key=True)
    trade_id = Column(String, ForeignKey("trades.id"), nullable=False, index=True)

    exception_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(Text, nullable=False)
    resolution_status = Column(String, default="OPEN")  # OPEN, IN_PROGRESS, RESOLVED

    # Processing
    assigned_to = Column(String)
    resolved_by = Column(String)
    resolution_notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

    # Relationships
    trade = relationship("Trade", back_populates="exceptions")


class ProcessingStep(Base):
    """Individual processing steps in trade lifecycle."""

    __tablename__ = "processing_steps"

    id = Column(String, primary_key=True)
    trade_id = Column(String, ForeignKey("trades.id"), nullable=False, index=True)

    step_name = Column(String, nullable=False)
    step_type = Column(
        String, nullable=False
    )  # VALIDATION, ENRICHMENT, MATCHING, CONFIRMATION, SETTLEMENT
    status = Column(
        String, nullable=False
    )  # PENDING, IN_PROGRESS, COMPLETED, FAILED, SKIPPED

    # Processing details
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Automation details
    automated = Column(Boolean, default=True)
    sop_document_id = Column(String)  # Reference to SOP in knowledge graph
    processor = Column(String)  # System/human who processed

    # Results
    result_data = Column(Text)  # JSON serialized results
    error_message = Column(Text)

    # Relationships
    trade = relationship("Trade", back_populates="processing_steps")


# Pydantic Models for API
class TradeBase(BaseModel):
    """Base trade model for API requests."""

    trade_reference: str
    counterparty_id: str
    instrument_id: str
    trade_type: TradeType
    side: str
    quantity: Decimal
    price: Decimal
    currency: str
    trade_date: datetime
    settlement_date: datetime
    value_date: Optional[datetime] = None


class TradeCreate(TradeBase):
    """Model for creating new trades."""

    pass


class TradeUpdate(BaseModel):
    """Model for updating trades."""

    status: Optional[TradeStatus] = None
    priority: Optional[Priority] = None
    requires_manual_review: Optional[bool] = None
    notes: Optional[str] = None


class TradeResponse(TradeBase):
    """Trade response model."""

    id: str
    trade_value: Decimal
    status: TradeStatus
    priority: Priority
    requires_manual_review: bool
    created_at: datetime
    updated_at: datetime
    processed_by: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class TradeExceptionCreate(BaseModel):
    """Model for creating trade exceptions."""

    trade_id: str
    exception_type: str
    severity: str
    description: str


class TradeExceptionResponse(BaseModel):
    """Trade exception response model."""

    id: str
    trade_id: str
    exception_type: str
    severity: str
    description: str
    resolution_status: str
    assigned_to: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProcessingStepCreate(BaseModel):
    """Model for creating processing steps."""

    trade_id: str
    step_name: str
    step_type: str
    sop_document_id: Optional[str] = None


class ProcessingStepResponse(BaseModel):
    """Processing step response model."""

    id: str
    trade_id: str
    step_name: str
    step_type: str
    status: str
    automated: bool
    sop_document_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    class Config:
        from_attributes = True
