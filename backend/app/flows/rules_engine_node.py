"""
Rules Engine Workflow Node for LangGraph Integration

This module provides LangGraph workflow nodes for integrating Vellum's
native JSON-first rules engine into custodian banking workflows. Supports
trade validation, risk management, compliance checks, and settlement
processing. Migrated off Drools/Kogito — see
docs/contracts/RULE_DEFINITION_CONTRACT.md.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from app.rules.engine import get_rule_engine
from app.rules.fact_builder import (
    build_compliance_facts,
    build_risk_management_facts,
    build_settlement_facts,
    build_trade_validation_facts,
)

logger = logging.getLogger(__name__)

# Action "type" values that indicate a hard failure, as emitted by
# RuleEngine.evaluate_rule_group's legacy-action mapping.
_VALIDATION_FAILURE_TYPES = {"ValidationError"}
_HIGH_SEVERITY = {"HIGH", "CRITICAL", "high", "critical"}


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
    """LangGraph node for trade validation using Vellum's native rules engine."""

    def __init__(self, config: RulesEngineConfig):
        self.config = config
        self.rule_engine = get_rule_engine()

    async def __call__(self, state: RulesEngineState) -> RulesEngineState:
        logger.info("Executing trade validation rules")

        try:
            trade_data = state.get("trade_data", {})
            if not trade_data:
                raise ValueError("No trade data provided for validation")

            facts = build_trade_validation_facts(trade_data)
            result = self.rule_engine.evaluate_rule_group("trade_validation", facts)

            validation_passed = result["status"] == "success" and not any(
                action.get("type") in _VALIDATION_FAILURE_TYPES
                for action in result["actions_triggered"]
            )

            updated_state = state.copy()
            updated_state["rule_results"].append(result)
            updated_state["validation_passed"] = validation_passed
            updated_state["alerts"].extend(result["actions_triggered"])
            updated_state["workflow_status"] = "validation_completed"
            updated_state["execution_metadata"]["validation_time"] = datetime.now().isoformat()

            logger.info(f"Trade validation completed: {'PASSED' if validation_passed else 'FAILED'}")
            return updated_state

        except Exception as e:
            logger.error(f"Trade validation failed: {str(e)}")

            error_state = state.copy()
            error_state["errors"].append(
                {"type": "VALIDATION_ERROR", "message": str(e), "timestamp": datetime.now().isoformat()}
            )
            error_state["validation_passed"] = False
            error_state["workflow_status"] = "validation_failed"

            return error_state


class RiskCheckNode:
    """LangGraph node for risk management using Vellum's native rules engine."""

    def __init__(self, config: RulesEngineConfig):
        self.config = config
        self.rule_engine = get_rule_engine()

    async def __call__(self, state: RulesEngineState) -> RulesEngineState:
        logger.info("Executing risk management rules")

        try:
            trade_data = state.get("trade_data", {})
            portfolio_data = state.get("portfolio_data", {})

            if not trade_data:
                raise ValueError("No trade data provided for risk check")
            if not portfolio_data:
                raise ValueError("No portfolio data provided for risk check")

            facts = build_risk_management_facts(trade_data, portfolio_data)
            result = self.rule_engine.evaluate_rule_group("risk_management", facts)

            risk_approved = result["status"] == "success" and not any(
                action.get("type") == "RiskAlert" and action.get("severity") in _HIGH_SEVERITY
                for action in result["actions_triggered"]
            )

            updated_state = state.copy()
            updated_state["rule_results"].append(result)
            updated_state["risk_approved"] = risk_approved
            updated_state["alerts"].extend(result["actions_triggered"])
            updated_state["workflow_status"] = "risk_check_completed"
            updated_state["execution_metadata"]["risk_check_time"] = datetime.now().isoformat()

            logger.info(f"Risk check completed: {'APPROVED' if risk_approved else 'REQUIRES_REVIEW'}")
            return updated_state

        except Exception as e:
            logger.error(f"Risk check failed: {str(e)}")

            error_state = state.copy()
            error_state["errors"].append(
                {"type": "RISK_CHECK_ERROR", "message": str(e), "timestamp": datetime.now().isoformat()}
            )
            error_state["risk_approved"] = False
            error_state["workflow_status"] = "risk_check_failed"

            return error_state


class ComplianceCheckNode:
    """LangGraph node for compliance checking using Vellum's native rules engine."""

    def __init__(self, config: RulesEngineConfig):
        self.config = config
        self.rule_engine = get_rule_engine()

    async def __call__(self, state: RulesEngineState) -> RulesEngineState:
        logger.info("Executing compliance rules")

        try:
            trade_data = state.get("trade_data", {})
            client_data = state.get("client_data", {})

            if not trade_data:
                raise ValueError("No trade data provided for compliance check")
            if not client_data:
                raise ValueError("No client data provided for compliance check")

            facts = build_compliance_facts(trade_data, client_data)
            result = self.rule_engine.evaluate_rule_group("compliance_checks", facts)

            compliance_approved = result["status"] == "success" and not any(
                action.get("type") == "ComplianceAlert" and action.get("severity") in _HIGH_SEVERITY
                for action in result["actions_triggered"]
            )

            updated_state = state.copy()
            updated_state["rule_results"].append(result)
            updated_state["compliance_approved"] = compliance_approved
            updated_state["alerts"].extend(result["actions_triggered"])
            updated_state["workflow_status"] = "compliance_check_completed"
            updated_state["execution_metadata"]["compliance_check_time"] = datetime.now().isoformat()

            logger.info(f"Compliance check completed: {'APPROVED' if compliance_approved else 'REQUIRES_REVIEW'}")
            return updated_state

        except Exception as e:
            logger.error(f"Compliance check failed: {str(e)}")

            error_state = state.copy()
            error_state["errors"].append(
                {"type": "COMPLIANCE_CHECK_ERROR", "message": str(e), "timestamp": datetime.now().isoformat()}
            )
            error_state["compliance_approved"] = False
            error_state["workflow_status"] = "compliance_check_failed"

            return error_state


class SettlementRulesNode:
    """LangGraph node for settlement processing using Vellum's native rules engine."""

    def __init__(self, config: RulesEngineConfig):
        self.config = config
        self.rule_engine = get_rule_engine()

    async def __call__(self, state: RulesEngineState) -> RulesEngineState:
        logger.info("Executing settlement processing rules")

        try:
            trade_data = state.get("trade_data", {})
            settlement_data = state.get("settlement_data", {})

            if not trade_data:
                raise ValueError("No trade data provided for settlement processing")
            if not settlement_data:
                raise ValueError("No settlement data provided for settlement processing")

            facts = build_settlement_facts(trade_data, settlement_data)
            result = self.rule_engine.evaluate_rule_group("settlement_processing", facts)

            settlement_approved = result["status"] == "success" and not any(
                action.get("type") == "SETTLEMENT_ERROR" for action in result["actions_triggered"]
            )

            updated_state = state.copy()
            updated_state["rule_results"].append(result)
            updated_state["settlement_approved"] = settlement_approved
            updated_state["alerts"].extend(result["actions_triggered"])
            updated_state["workflow_status"] = "settlement_processing_completed"
            updated_state["execution_metadata"]["settlement_processing_time"] = datetime.now().isoformat()

            logger.info(f"Settlement processing completed: {'APPROVED' if settlement_approved else 'REQUIRES_REVIEW'}")
            return updated_state

        except Exception as e:
            logger.error(f"Settlement processing failed: {str(e)}")

            error_state = state.copy()
            error_state["errors"].append(
                {"type": "SETTLEMENT_PROCESSING_ERROR", "message": str(e), "timestamp": datetime.now().isoformat()}
            )
            error_state["settlement_approved"] = False
            error_state["workflow_status"] = "settlement_processing_failed"

            return error_state


def create_trade_processing_workflow(config: RulesEngineConfig) -> StateGraph:
    """Create a complete trade processing workflow with rules engine integration"""
    validation_node = TradeValidationNode(config)
    risk_node = RiskCheckNode(config)
    compliance_node = ComplianceCheckNode(config)
    settlement_node = SettlementRulesNode(config)

    workflow = StateGraph(RulesEngineState)

    workflow.add_node("validate_trade", validation_node)
    workflow.add_node("check_risk", risk_node)
    workflow.add_node("check_compliance", compliance_node)
    workflow.add_node("process_settlement", settlement_node)

    workflow.set_entry_point("validate_trade")

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
    """Create initial state for rules engine workflow"""
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
