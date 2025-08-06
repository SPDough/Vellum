"""
Rules Engine Workflow Node for LangGraph Integration

This module provides LangGraph workflow nodes for integrating Drools rules engine
into custodian banking workflows. Supports trade validation, risk management,
compliance checks, and settlement processing.
"""

import json
import logging
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from app.models.trade import Trade
from app.models.workflow import NodeType, WorkflowExecution, WorkflowNode
from app.services.drools_service import (
    RuleExecutionStatus,
    RuleFact,
    RuleResult,
    get_drools_service,
)

logger = logging.getLogger(__name__)


class RulesEngineState(TypedDict):
    """State structure for rules engine workflow nodes"""

    trade_data: Dict[str, Any]
    portfolio_data: Optional[Dict[str, Any]]
    client_data: Optional[Dict[str, Any]]
    settlement_data: Optional[Dict[str, Any]]
    rule_results: List[Dict[str, Any]]
    validation_passed: bool
    risk_approved: bool
    compliance_approved: bool
    settlement_approved: bool
    alerts: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    workflow_status: str
    execution_metadata: Dict[str, Any]


class RulesEngineConfig(BaseModel):
    """Configuration for rules engine workflow node"""

    rule_sets: List[str] = Field(
        default=["trade-validation"], description="Rule sets to execute"
    )
    timeout_seconds: int = Field(default=30, description="Execution timeout")
    require_all_passed: bool = Field(
        default=True, description="Require all rule sets to pass"
    )
    enable_parallel_execution: bool = Field(
        default=False, description="Execute rule sets in parallel"
    )
    log_level: str = Field(default="INFO", description="Logging level")


class TradeValidationNode:
    """
    LangGraph node for trade validation using Drools rules
    """

    def __init__(self, config: RulesEngineConfig):
        self.config = config
        self.drools_service = get_drools_service()

    async def __call__(self, state: RulesEngineState) -> RulesEngineState:
        """
        Execute trade validation rules

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state with validation results
        """
        logger.info("Executing trade validation rules")

        try:
            # Extract trade data from state
            trade_data = state.get("trade_data", {})
            if not trade_data:
                raise ValueError("No trade data provided for validation")

            # Create trade fact for rules engine
            trade_fact = RuleFact(
                fact_type="Trade",
                fact_id=str(trade_data.get("tradeId", "unknown")),
                data=trade_data,
                timestamp=datetime.now(),
            )

            # Execute validation rules
            async with self.drools_service:
                result = await self.drools_service.execute_rules(
                    rule_set="trade-validation",
                    facts=[trade_fact],
                    timeout_seconds=self.config.timeout_seconds,
                )

            # Process results
            validation_passed = (
                result.status == RuleExecutionStatus.SUCCESS
                and not any(
                    action.get("type") == "VALIDATION_ERROR"
                    for action in result.actions_triggered
                )
            )

            # Update state
            updated_state = state.copy()
            updated_state["rule_results"].append(result.to_dict())
            updated_state["validation_passed"] = validation_passed

            # Add any alerts from rule execution
            for action in result.actions_triggered:
                if action.get("type") in ["Alert", "ValidationError"]:
                    updated_state["alerts"].append(action)

            updated_state["workflow_status"] = "validation_completed"
            updated_state["execution_metadata"][
                "validation_time"
            ] = datetime.now().isoformat()

            logger.info(
                f"Trade validation completed: {'PASSED' if validation_passed else 'FAILED'}"
            )
            return updated_state

        except Exception as e:
            logger.error(f"Trade validation failed: {str(e)}")

            error_state = state.copy()
            error_state["errors"].append(
                {
                    "type": "VALIDATION_ERROR",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            error_state["validation_passed"] = False
            error_state["workflow_status"] = "validation_failed"

            return error_state


class RiskCheckNode:
    """
    LangGraph node for risk management using Drools rules
    """

    def __init__(self, config: RulesEngineConfig):
        self.config = config
        self.drools_service = get_drools_service()

    async def __call__(self, state: RulesEngineState) -> RulesEngineState:
        """
        Execute risk management rules

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state with risk check results
        """
        logger.info("Executing risk management rules")

        try:
            # Extract data from state
            trade_data = state.get("trade_data", {})
            portfolio_data = state.get("portfolio_data", {})

            if not trade_data:
                raise ValueError("No trade data provided for risk check")
            if not portfolio_data:
                raise ValueError("No portfolio data provided for risk check")

            # Create facts for rules engine
            facts = [
                RuleFact(
                    fact_type="Trade",
                    fact_id=str(trade_data.get("tradeId", "unknown")),
                    data=trade_data,
                    timestamp=datetime.now(),
                ),
                RuleFact(
                    fact_type="Portfolio",
                    fact_id=trade_data.get("portfolio", "unknown"),
                    data=portfolio_data,
                    timestamp=datetime.now(),
                ),
            ]

            # Execute risk rules
            async with self.drools_service:
                result = await self.drools_service.execute_rules(
                    rule_set="risk-management",
                    facts=facts,
                    timeout_seconds=self.config.timeout_seconds,
                )

            # Process results
            risk_approved = result.status == RuleExecutionStatus.SUCCESS and not any(
                action.get("type") == "RISK_ALERT" and action.get("severity") == "HIGH"
                for action in result.actions_triggered
            )

            # Update state
            updated_state = state.copy()
            updated_state["rule_results"].append(result.to_dict())
            updated_state["risk_approved"] = risk_approved

            # Add any alerts from rule execution
            for action in result.actions_triggered:
                if action.get("type") in ["RiskAlert", "Alert"]:
                    updated_state["alerts"].append(action)

            updated_state["workflow_status"] = "risk_check_completed"
            updated_state["execution_metadata"][
                "risk_check_time"
            ] = datetime.now().isoformat()

            logger.info(
                f"Risk check completed: {'APPROVED' if risk_approved else 'REQUIRES_REVIEW'}"
            )
            return updated_state

        except Exception as e:
            logger.error(f"Risk check failed: {str(e)}")

            error_state = state.copy()
            error_state["errors"].append(
                {
                    "type": "RISK_CHECK_ERROR",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            error_state["risk_approved"] = False
            error_state["workflow_status"] = "risk_check_failed"

            return error_state


class ComplianceCheckNode:
    """
    LangGraph node for compliance checking using Drools rules
    """

    def __init__(self, config: RulesEngineConfig):
        self.config = config
        self.drools_service = get_drools_service()

    async def __call__(self, state: RulesEngineState) -> RulesEngineState:
        """
        Execute compliance rules

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state with compliance check results
        """
        logger.info("Executing compliance rules")

        try:
            # Extract data from state
            trade_data = state.get("trade_data", {})
            client_data = state.get("client_data", {})

            if not trade_data:
                raise ValueError("No trade data provided for compliance check")
            if not client_data:
                raise ValueError("No client data provided for compliance check")

            # Create facts for rules engine
            facts = [
                RuleFact(
                    fact_type="Trade",
                    fact_id=str(trade_data.get("tradeId", "unknown")),
                    data=trade_data,
                    timestamp=datetime.now(),
                ),
                RuleFact(
                    fact_type="Client",
                    fact_id=trade_data.get("counterpartyId", "unknown"),
                    data=client_data,
                    timestamp=datetime.now(),
                ),
            ]

            # Execute compliance rules
            async with self.drools_service:
                result = await self.drools_service.execute_rules(
                    rule_set="compliance-checks",
                    facts=facts,
                    timeout_seconds=self.config.timeout_seconds,
                )

            # Process results
            compliance_approved = (
                result.status == RuleExecutionStatus.SUCCESS
                and not any(
                    action.get("type") == "COMPLIANCE_ALERT"
                    and action.get("severity") in ["HIGH", "CRITICAL"]
                    for action in result.actions_triggered
                )
            )

            # Update state
            updated_state = state.copy()
            updated_state["rule_results"].append(result.to_dict())
            updated_state["compliance_approved"] = compliance_approved

            # Add any alerts from rule execution
            for action in result.actions_triggered:
                if action.get("type") in ["ComplianceAlert", "Alert"]:
                    updated_state["alerts"].append(action)

            updated_state["workflow_status"] = "compliance_check_completed"
            updated_state["execution_metadata"][
                "compliance_check_time"
            ] = datetime.now().isoformat()

            logger.info(
                f"Compliance check completed: {'APPROVED' if compliance_approved else 'REQUIRES_REVIEW'}"
            )
            return updated_state

        except Exception as e:
            logger.error(f"Compliance check failed: {str(e)}")

            error_state = state.copy()
            error_state["errors"].append(
                {
                    "type": "COMPLIANCE_CHECK_ERROR",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            error_state["compliance_approved"] = False
            error_state["workflow_status"] = "compliance_check_failed"

            return error_state


class SettlementRulesNode:
    """
    LangGraph node for settlement processing using Drools rules
    """

    def __init__(self, config: RulesEngineConfig):
        self.config = config
        self.drools_service = get_drools_service()

    async def __call__(self, state: RulesEngineState) -> RulesEngineState:
        """
        Execute settlement processing rules

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state with settlement processing results
        """
        logger.info("Executing settlement processing rules")

        try:
            # Extract data from state
            trade_data = state.get("trade_data", {})
            settlement_data = state.get("settlement_data", {})

            if not trade_data:
                raise ValueError("No trade data provided for settlement processing")
            if not settlement_data:
                raise ValueError(
                    "No settlement data provided for settlement processing"
                )

            # Create facts for rules engine
            facts = [
                RuleFact(
                    fact_type="Trade",
                    fact_id=str(trade_data.get("tradeId", "unknown")),
                    data=trade_data,
                    timestamp=datetime.now(),
                ),
                RuleFact(
                    fact_type="Settlement",
                    fact_id=f"settlement_{trade_data.get('tradeId', 'unknown')}",
                    data=settlement_data,
                    timestamp=datetime.now(),
                ),
            ]

            # Execute settlement rules
            async with self.drools_service:
                result = await self.drools_service.execute_rules(
                    rule_set="settlement-processing",
                    facts=facts,
                    timeout_seconds=self.config.timeout_seconds,
                )

            # Process results
            settlement_approved = (
                result.status == RuleExecutionStatus.SUCCESS
                and not any(
                    action.get("type") == "SETTLEMENT_ERROR"
                    for action in result.actions_triggered
                )
            )

            # Update state
            updated_state = state.copy()
            updated_state["rule_results"].append(result.to_dict())
            updated_state["settlement_approved"] = settlement_approved

            # Add any alerts from rule execution
            for action in result.actions_triggered:
                if action.get("type") in ["Alert", "SettlementAlert"]:
                    updated_state["alerts"].append(action)

            updated_state["workflow_status"] = "settlement_processing_completed"
            updated_state["execution_metadata"][
                "settlement_processing_time"
            ] = datetime.now().isoformat()

            logger.info(
                f"Settlement processing completed: {'APPROVED' if settlement_approved else 'REQUIRES_REVIEW'}"
            )
            return updated_state

        except Exception as e:
            logger.error(f"Settlement processing failed: {str(e)}")

            error_state = state.copy()
            error_state["errors"].append(
                {
                    "type": "SETTLEMENT_PROCESSING_ERROR",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            error_state["settlement_approved"] = False
            error_state["workflow_status"] = "settlement_processing_failed"

            return error_state


def create_trade_processing_workflow(config: RulesEngineConfig) -> StateGraph:
    """
    Create a complete trade processing workflow with rules engine integration

    Args:
        config: Configuration for rules engine nodes

    Returns:
        StateGraph: Complete trade processing workflow
    """
    # Initialize workflow nodes
    validation_node = TradeValidationNode(config)
    risk_node = RiskCheckNode(config)
    compliance_node = ComplianceCheckNode(config)
    settlement_node = SettlementRulesNode(config)

    # Create state graph
    workflow = StateGraph(RulesEngineState)

    # Add nodes
    workflow.add_node("validate_trade", validation_node)
    workflow.add_node("check_risk", risk_node)
    workflow.add_node("check_compliance", compliance_node)
    workflow.add_node("process_settlement", settlement_node)

    # Define workflow flow
    workflow.set_entry_point("validate_trade")

    # Conditional edges based on rule results
    workflow.add_conditional_edges(
        "validate_trade",
        lambda state: "check_risk" if state["validation_passed"] else END,
    )

    workflow.add_conditional_edges(
        "check_risk",
        lambda state: "check_compliance" if state["risk_approved"] else END,
    )

    workflow.add_conditional_edges(
        "check_compliance",
        lambda state: "process_settlement" if state["compliance_approved"] else END,
    )

    workflow.add_edge("process_settlement", END)

    return workflow.compile()


def create_initial_state(
    trade_data: Dict[str, Any],
    portfolio_data: Optional[Dict[str, Any]] = None,
    client_data: Optional[Dict[str, Any]] = None,
    settlement_data: Optional[Dict[str, Any]] = None,
) -> RulesEngineState:
    """
    Create initial state for rules engine workflow

    Args:
        trade_data: Trade information
        portfolio_data: Portfolio information (optional)
        client_data: Client information (optional)
        settlement_data: Settlement information (optional)

    Returns:
        RulesEngineState: Initial workflow state
    """
    return RulesEngineState(
        trade_data=trade_data,
        portfolio_data=portfolio_data,
        client_data=client_data,
        settlement_data=settlement_data,
        rule_results=[],
        validation_passed=False,
        risk_approved=False,
        compliance_approved=False,
        settlement_approved=False,
        alerts=[],
        errors=[],
        workflow_status="initialized",
        execution_metadata={
            "start_time": datetime.now().isoformat(),
            "workflow_id": f"rules_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        },
    )
