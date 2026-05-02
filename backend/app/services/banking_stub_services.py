"""
Stub implementations for banking service interfaces.

Used by ServiceFactory until real trade/risk/compliance/user/SOP/audit services exist.
All business methods return a clear not-implemented outcome instead of failing imports.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.base import OperationResult, ServiceContext
from app.services.interfaces import (
    IAuditService,
    IComplianceService,
    IRiskService,
    ISOPService,
    ITradeService,
    IUserService,
)


def _not_implemented(service: str, operation: str) -> OperationResult:
    return OperationResult(
        success=False,
        message=None,
        errors=[f"{service}.{operation} is not implemented yet"],
    )


class StubTradeService(ITradeService):
    async def create_trade(
        self, trade_data: Dict[str, Any], context: ServiceContext
    ) -> OperationResult:
        return _not_implemented("TradeService", "create_trade")

    async def execute_trade_workflow(
        self, trade_id: str, context: ServiceContext
    ) -> OperationResult:
        return _not_implemented("TradeService", "execute_trade_workflow")

    async def get_trade_status(
        self, trade_id: str, context: ServiceContext
    ) -> OperationResult:
        return _not_implemented("TradeService", "get_trade_status")


class StubSOPService(ISOPService):
    async def create_sop_document(
        self, sop_data: Dict[str, Any], context: ServiceContext
    ) -> OperationResult:
        return _not_implemented("SOPService", "create_sop_document")

    async def get_sop_by_category(
        self, category: str, context: ServiceContext
    ) -> OperationResult:
        return _not_implemented("SOPService", "get_sop_by_category")

    async def execute_sop(
        self, sop_id: str, execution_data: Dict[str, Any], context: ServiceContext
    ) -> OperationResult:
        return _not_implemented("SOPService", "execute_sop")


class StubRiskService(IRiskService):
    async def assess_trade_risk(
        self, trade_data: Dict[str, Any], context: ServiceContext
    ) -> OperationResult:
        return _not_implemented("RiskService", "assess_trade_risk")

    async def monitor_portfolio_risk(
        self, portfolio_id: str, context: ServiceContext
    ) -> OperationResult:
        return _not_implemented("RiskService", "monitor_portfolio_risk")

    async def check_risk_limits(
        self, entity_type: str, entity_id: str, context: ServiceContext
    ) -> OperationResult:
        return _not_implemented("RiskService", "check_risk_limits")


class StubComplianceService(IComplianceService):
    async def validate_kyc_status(
        self, customer_id: str, context: ServiceContext
    ) -> OperationResult:
        return _not_implemented("ComplianceService", "validate_kyc_status")

    async def perform_compliance_check(
        self, check_type: str, data: Dict[str, Any], context: ServiceContext
    ) -> OperationResult:
        return _not_implemented("ComplianceService", "perform_compliance_check")

    async def generate_compliance_report(
        self, report_type: str, parameters: Dict[str, Any], context: ServiceContext
    ) -> OperationResult:
        return _not_implemented("ComplianceService", "generate_compliance_report")


class StubUserService(IUserService):
    async def authenticate_user(
        self, credentials: Dict[str, Any], context: ServiceContext
    ) -> OperationResult:
        return _not_implemented("UserService", "authenticate_user")

    async def authorize_action(
        self, user_id: str, action: str, resource: str, context: ServiceContext
    ) -> OperationResult:
        return _not_implemented("UserService", "authorize_action")

    async def update_user_profile(
        self, user_id: str, profile_data: Dict[str, Any], context: ServiceContext
    ) -> OperationResult:
        return _not_implemented("UserService", "update_user_profile")


class StubAuditService(IAuditService):
    async def log_operation(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        **kwargs: Any,
    ) -> None:
        return None

    async def get_audit_trail(
        self, resource_type: str, resource_id: str, context: ServiceContext
    ) -> OperationResult:
        return _not_implemented("AuditService", "get_audit_trail")
