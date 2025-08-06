"""
Service interfaces and protocols for Otomeshon Banking Platform
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from decimal import Decimal
from datetime import datetime, date
from enum import Enum

from pydantic import BaseModel

from app.services.base import ServiceContext, OperationResult


class TradeStatus(Enum):
    """Trade status enumeration"""
    NEW = "NEW"
    VALIDATED = "VALIDATED"
    PENDING_SETTLEMENT = "PENDING_SETTLEMENT"
    SETTLED = "SETTLED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SOPExecutionStatus(Enum):
    """SOP execution status enumeration"""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"


class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Trading Service Interfaces

@runtime_checkable
class TradeValidationProtocol(Protocol):
    """Protocol for trade validation services"""

    async def validate_trade(
        self,
        symbol: str,
        quantity: int,
        price: Decimal,
        side: str,
        context: ServiceContext
    ) -> OperationResult:
        """Validate a trade before execution"""
        ...

    async def check_position_limits(
        self,
        account: str,
        symbol: str,
        quantity: int,
        context: ServiceContext
    ) -> OperationResult:
        """Check if trade exceeds position limits"""
        ...


@runtime_checkable
class SettlementProtocol(Protocol):
    """Protocol for trade settlement services"""

    async def initiate_settlement(
        self,
        trade_id: str,
        context: ServiceContext
    ) -> OperationResult:
        """Initiate trade settlement process"""
        ...

    async def confirm_settlement(
        self,
        trade_id: str,
        settlement_data: Dict[str, Any],
        context: ServiceContext
    ) -> OperationResult:
        """Confirm settlement completion"""
        ...


class ITradeService(ABC):
    """Abstract interface for trade services"""

    @abstractmethod
    async def create_trade(
        self,
        trade_data: Dict[str, Any],
        context: ServiceContext
    ) -> OperationResult:
        """Create a new trade"""
        pass

    @abstractmethod
    async def execute_trade_workflow(
        self,
        trade_id: str,
        context: ServiceContext
    ) -> OperationResult:
        """Execute complete trade workflow"""
        pass

    @abstractmethod
    async def get_trade_status(
        self,
        trade_id: str,
        context: ServiceContext
    ) -> OperationResult:
        """Get current trade status"""
        pass


# SOP Service Interfaces

@runtime_checkable
class SOPExecutionProtocol(Protocol):
    """Protocol for SOP execution services"""

    async def start_execution(
        self,
        sop_id: str,
        execution_data: Dict[str, Any],
        context: ServiceContext
    ) -> OperationResult:
        """Start SOP execution"""
        ...

    async def execute_step(
        self,
        execution_id: str,
        step_id: str,
        step_data: Dict[str, Any],
        context: ServiceContext
    ) -> OperationResult:
        """Execute a specific SOP step"""
        ...

    async def complete_execution(
        self,
        execution_id: str,
        context: ServiceContext
    ) -> OperationResult:
        """Complete SOP execution"""
        ...


class ISOPService(ABC):
    """Abstract interface for SOP services"""

    @abstractmethod
    async def create_sop_document(
        self,
        sop_data: Dict[str, Any],
        context: ServiceContext
    ) -> OperationResult:
        """Create a new SOP document"""
        pass

    @abstractmethod
    async def get_sop_by_category(
        self,
        category: str,
        context: ServiceContext
    ) -> OperationResult:
        """Get SOPs by category"""
        pass

    @abstractmethod
    async def execute_sop(
        self,
        sop_id: str,
        execution_data: Dict[str, Any],
        context: ServiceContext
    ) -> OperationResult:
        """Execute an SOP"""
        pass


# Risk Management Interfaces

@runtime_checkable
class RiskCalculationProtocol(Protocol):
    """Protocol for risk calculation services"""

    async def calculate_var(
        self,
        portfolio_id: str,
        confidence_level: float,
        time_horizon: int,
        context: ServiceContext
    ) -> OperationResult:
        """Calculate Value at Risk"""
        ...

    async def calculate_position_risk(
        self,
        position_data: Dict[str, Any],
        context: ServiceContext
    ) -> OperationResult:
        """Calculate individual position risk"""
        ...


class IRiskService(ABC):
    """Abstract interface for risk management services"""

    @abstractmethod
    async def assess_trade_risk(
        self,
        trade_data: Dict[str, Any],
        context: ServiceContext
    ) -> OperationResult:
        """Assess risk for a trade"""
        pass

    @abstractmethod
    async def monitor_portfolio_risk(
        self,
        portfolio_id: str,
        context: ServiceContext
    ) -> OperationResult:
        """Monitor portfolio risk metrics"""
        pass

    @abstractmethod
    async def check_risk_limits(
        self,
        entity_type: str,
        entity_id: str,
        context: ServiceContext
    ) -> OperationResult:
        """Check if entity exceeds risk limits"""
        pass


# Compliance Interfaces

@runtime_checkable
class ComplianceCheckProtocol(Protocol):
    """Protocol for compliance checking services"""

    async def check_aml_compliance(
        self,
        transaction_data: Dict[str, Any],
        context: ServiceContext
    ) -> OperationResult:
        """Check AML compliance"""
        ...

    async def check_trading_rules(
        self,
        trade_data: Dict[str, Any],
        context: ServiceContext
    ) -> OperationResult:
        """Check trading rule compliance"""
        ...


class IComplianceService(ABC):
    """Abstract interface for compliance services"""

    @abstractmethod
    async def validate_kyc_status(
        self,
        customer_id: str,
        context: ServiceContext
    ) -> OperationResult:
        """Validate customer KYC status"""
        pass

    @abstractmethod
    async def perform_compliance_check(
        self,
        check_type: str,
        data: Dict[str, Any],
        context: ServiceContext
    ) -> OperationResult:
        """Perform specific compliance check"""
        pass

    @abstractmethod
    async def generate_compliance_report(
        self,
        report_type: str,
        parameters: Dict[str, Any],
        context: ServiceContext
    ) -> OperationResult:
        """Generate compliance report"""
        pass


# User Management Interfaces

class IUserService(ABC):
    """Abstract interface for user management services"""

    @abstractmethod
    async def authenticate_user(
        self,
        credentials: Dict[str, Any],
        context: ServiceContext
    ) -> OperationResult:
        """Authenticate user credentials"""
        pass

    @abstractmethod
    async def authorize_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        context: ServiceContext
    ) -> OperationResult:
        """Authorize user action on resource"""
        pass

    @abstractmethod
    async def update_user_profile(
        self,
        user_id: str,
        profile_data: Dict[str, Any],
        context: ServiceContext
    ) -> OperationResult:
        """Update user profile"""
        pass


# Audit and Reporting Interfaces

class IAuditService(ABC):
    """Abstract interface for audit services"""

    @abstractmethod
    async def log_operation(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        **kwargs
    ) -> None:
        """Log an operation for audit"""
        pass

    @abstractmethod
    async def get_audit_trail(
        self,
        resource_type: str,
        resource_id: str,
        context: ServiceContext
    ) -> OperationResult:
        """Get audit trail for resource"""
        pass

    @abstractmethod
    async def generate_audit_report(
        self,
        start_date: date,
        end_date: date,
        context: ServiceContext
    ) -> OperationResult:
        """Generate audit report"""
        pass


# Data and Analytics Interfaces

class IDataService(ABC):
    """Abstract interface for data management services"""

    @abstractmethod
    async def store_data_record(
        self,
        data: Dict[str, Any],
        source: str,
        data_type: str,
        context: ServiceContext
    ) -> OperationResult:
        """Store a data record"""
        pass

    @abstractmethod
    async def query_data(
        self,
        query_params: Dict[str, Any],
        context: ServiceContext
    ) -> OperationResult:
        """Query stored data"""
        pass


# Workflow and Integration Interfaces

class IWorkflowService(ABC):
    """Abstract interface for workflow execution services"""

    @abstractmethod
    async def start_workflow(
        self,
        workflow_type: str,
        input_data: Dict[str, Any],
        context: ServiceContext
    ) -> OperationResult:
        """Start a workflow execution"""
        pass

    @abstractmethod
    async def get_workflow_status(
        self,
        workflow_id: str,
        context: ServiceContext
    ) -> OperationResult:
        """Get workflow execution status"""
        pass


class INotificationService(ABC):
    """Abstract interface for notification services"""

    @abstractmethod
    async def send_notification(
        self,
        recipient: str,
        message: str,
        notification_type: str,
        context: ServiceContext
    ) -> OperationResult:
        """Send a notification"""
        pass

    @abstractmethod
    async def send_alert(
        self,
        alert_type: str,
        message: str,
        severity: str,
        context: ServiceContext
    ) -> OperationResult:
        """Send an alert"""
        pass


# Service Factory Interface

class IServiceFactory(ABC):
    """Abstract factory for creating service instances"""

    @abstractmethod
    def create_trade_service(self) -> ITradeService:
        """Create trade service instance"""
        pass

    @abstractmethod
    def create_sop_service(self) -> ISOPService:
        """Create SOP service instance"""
        pass

    @abstractmethod
    def create_risk_service(self) -> IRiskService:
        """Create risk service instance"""
        pass

    @abstractmethod
    def create_compliance_service(self) -> IComplianceService:
        """Create compliance service instance"""
        pass

    @abstractmethod
    def create_user_service(self) -> IUserService:
        """Create user service instance"""
        pass

    @abstractmethod
    def create_audit_service(self) -> IAuditService:
        """Create audit service instance"""
        pass