"""
Unified Workflow Execution Service for Otomeshon Custodian Portal

This service provides a unified interface for executing both rules-based and
agent-based workflows for custodian banking operations. Combines Drools rules
engine with LangGraph agent workflows for comprehensive automation.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from app.core.config import get_settings
from app.flows.rules_engine_node import (
    ComplianceCheckNode,
    RiskCheckNode,
    RulesEngineConfig,
    TradeValidationNode,
    create_initial_state,
)
from app.models.workflow import (
    NodeType,
    WorkflowExecution,
    WorkflowNode,
    WorkflowStatus,
)
from app.services.drools_service import RuleFact, get_drools_service

logger = logging.getLogger(__name__)


class WorkflowType(str, Enum):
    """Types of workflows supported"""

    RULES_BASED = "rules_based"
    AGENT_BASED = "agent_based"
    HYBRID = "hybrid"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


class NodeExecutionStatus(str, Enum):
    """Status of individual node execution"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"


@dataclass
class WorkflowNodeConfig:
    """Configuration for a workflow node"""

    node_id: str
    node_type: str  # RULES_ENGINE, AGENT, TRANSFORM, DECISION, etc.
    name: str
    description: str
    config: Dict[str, Any]
    dependencies: Optional[List[str]] = None
    conditions: Optional[Dict[str, Any]] = None
    timeout_seconds: int = 300
    retry_count: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WorkflowConfig:
    """Complete workflow configuration"""

    workflow_id: str
    name: str
    description: str
    workflow_type: WorkflowType
    nodes: List[WorkflowNodeConfig]
    entry_point: str
    exit_conditions: Dict[str, Any]
    global_timeout_seconds: int = 3600
    enable_monitoring: bool = True
    enable_audit: bool = True
    created_by: str = "system"
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NodeExecutionResult:
    """Result of executing a single workflow node"""

    node_id: str
    node_type: str
    status: NodeExecutionStatus
    start_time: datetime
    end_time: Optional[datetime]
    execution_time_ms: float
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    error_message: Optional[str] = None

    alerts: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # Convert datetime objects to ISO strings
        result["start_time"] = self.start_time.isoformat()
        result["end_time"] = self.end_time.isoformat() if self.end_time else None
        return result


@dataclass
class WorkflowExecutionResult:
    """Result of complete workflow execution"""

    workflow_id: str
    execution_id: str
    status: WorkflowStatus
    start_time: datetime
    end_time: Optional[datetime]
    total_execution_time_ms: float
    node_results: List[NodeExecutionResult]
    final_output: Dict[str, Any]
    summary: Dict[str, Any]
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["start_time"] = self.start_time.isoformat()
        result["end_time"] = self.end_time.isoformat() if self.end_time else None
        result["node_results"] = [nr.to_dict() for nr in self.node_results]
        return result


class WorkflowExecutionService:
    """
    Service for executing configured workflows with both rules and agents
    """

    def __init__(self):
        self.settings = get_settings()
        self.drools_service = get_drools_service()
        self.active_executions: Dict[str, WorkflowExecutionResult] = {}
        self.workflow_templates: Dict[str, WorkflowConfig] = {}

        # Initialize built-in workflow templates
        self._initialize_builtin_templates()

    def _initialize_builtin_templates(self):
        """Initialize built-in workflow templates for custodian banking"""

        # Trade Processing Workflow
        trade_processing = WorkflowConfig(
            workflow_id="trade_processing_v1",
            name="Trade Processing Workflow",
            description="Complete trade processing with validation, risk, compliance, and settlement",
            workflow_type=WorkflowType.SEQUENTIAL,
            nodes=[
                WorkflowNodeConfig(
                    node_id="validate_trade",
                    node_type="RULES_ENGINE",
                    name="Trade Validation",
                    description="Validate trade data using business rules",
                    config={
                        "rule_sets": ["trade-validation"],
                        "timeout_seconds": 30,
                        "require_all_passed": True,
                    },
                ),
                WorkflowNodeConfig(
                    node_id="check_risk",
                    node_type="RULES_ENGINE",
                    name="Risk Assessment",
                    description="Assess risk limits and concentration",
                    config={"rule_sets": ["risk-management"], "timeout_seconds": 45},
                    dependencies=["validate_trade"],
                    conditions={"validate_trade.validation_passed": True},
                ),
                WorkflowNodeConfig(
                    node_id="compliance_check",
                    node_type="RULES_ENGINE",
                    name="Compliance Screening",
                    description="KYC, AML, and sanctions screening",
                    config={"rule_sets": ["compliance-checks"], "timeout_seconds": 60},
                    dependencies=["check_risk"],
                    conditions={"check_risk.risk_approved": True},
                ),
                WorkflowNodeConfig(
                    node_id="settlement_processing",
                    node_type="RULES_ENGINE",
                    name="Settlement Processing",
                    description="Process settlement instructions and validations",
                    config={
                        "rule_sets": ["settlement-processing"],
                        "timeout_seconds": 90,
                    },
                    dependencies=["compliance_check"],
                    conditions={"compliance_check.compliance_approved": True},
                ),
                WorkflowNodeConfig(
                    node_id="generate_confirmations",
                    node_type="AGENT",
                    name="Generate Trade Confirmations",
                    description="Generate and send trade confirmations using AI agent",
                    config={
                        "agent_type": "document_generator",
                        "template": "trade_confirmation",
                        "output_format": "pdf",
                    },
                    dependencies=["settlement_processing"],
                ),
            ],
            entry_point="validate_trade",
            exit_conditions={
                "success": "generate_confirmations.status == 'completed'",
                "failure": "any(node.status == 'failed' for node in nodes)",
            },
        )

        # Exception Handling Workflow
        exception_handling = WorkflowConfig(
            workflow_id="exception_handling_v1",
            name="Trade Exception Handling",
            description="Handle trade exceptions with AI-powered analysis and resolution",
            workflow_type=WorkflowType.HYBRID,
            nodes=[
                WorkflowNodeConfig(
                    node_id="classify_exception",
                    node_type="AGENT",
                    name="Classify Exception",
                    description="Use AI to classify and prioritize the exception",
                    config={
                        "agent_type": "classifier",
                        "model": "gpt-4",
                        "classification_types": [
                            "data_quality",
                            "risk_breach",
                            "compliance_issue",
                            "operational_error",
                        ],
                    },
                ),
                WorkflowNodeConfig(
                    node_id="check_auto_resolution_rules",
                    node_type="RULES_ENGINE",
                    name="Auto-Resolution Rules",
                    description="Check if exception can be auto-resolved",
                    config={
                        "rule_sets": ["exception-auto-resolution"],
                        "timeout_seconds": 30,
                    },
                    dependencies=["classify_exception"],
                ),
                WorkflowNodeConfig(
                    node_id="escalate_manual_review",
                    node_type="DECISION",
                    name="Manual Review Decision",
                    description="Decide if manual review is required",
                    config={
                        "decision_logic": "not check_auto_resolution_rules.can_auto_resolve"
                    },
                    dependencies=["check_auto_resolution_rules"],
                ),
                WorkflowNodeConfig(
                    node_id="ai_resolution_suggestions",
                    node_type="AGENT",
                    name="AI Resolution Suggestions",
                    description="Generate resolution suggestions using AI",
                    config={
                        "agent_type": "advisor",
                        "model": "gpt-4",
                        "expertise": "custodian_banking_operations",
                    },
                    dependencies=["escalate_manual_review"],
                    conditions={"escalate_manual_review.requires_manual_review": True},
                ),
            ],
            entry_point="classify_exception",
            exit_conditions={
                "auto_resolved": "check_auto_resolution_rules.can_auto_resolve == True",
                "manual_review": "ai_resolution_suggestions.status == 'completed'",
            },
        )

        # Client Onboarding Workflow
        client_onboarding = WorkflowConfig(
            workflow_id="client_onboarding_v1",
            name="Client Onboarding Workflow",
            description="Complete client onboarding with KYC, documentation, and setup",
            workflow_type=WorkflowType.PARALLEL,
            nodes=[
                WorkflowNodeConfig(
                    node_id="document_collection",
                    node_type="AGENT",
                    name="Document Collection",
                    description="AI-powered document collection and validation",
                    config={
                        "agent_type": "document_processor",
                        "required_documents": [
                            "identity",
                            "address_proof",
                            "financial_statements",
                        ],
                        "ocr_enabled": True,
                    },
                ),
                WorkflowNodeConfig(
                    node_id="kyc_screening",
                    node_type="RULES_ENGINE",
                    name="KYC Screening",
                    description="Automated KYC screening and verification",
                    config={
                        "rule_sets": ["kyc-screening", "sanctions-check"],
                        "external_apis": ["world_check", "lexis_nexis"],
                    },
                ),
                WorkflowNodeConfig(
                    node_id="credit_assessment",
                    node_type="AGENT",
                    name="Credit Assessment",
                    description="AI-powered credit and risk assessment",
                    config={
                        "agent_type": "risk_assessor",
                        "model": "gpt-4",
                        "assessment_criteria": [
                            "financial_strength",
                            "regulatory_standing",
                            "operational_risk",
                        ],
                    },
                ),
                WorkflowNodeConfig(
                    node_id="final_approval",
                    node_type="DECISION",
                    name="Final Approval Decision",
                    description="Make final onboarding decision",
                    config={
                        "decision_logic": "all([kyc_screening.approved, credit_assessment.approved, document_collection.completed])"
                    },
                    dependencies=[
                        "document_collection",
                        "kyc_screening",
                        "credit_assessment",
                    ],
                ),
            ],
            entry_point="parallel_start",
            exit_conditions={
                "approved": "final_approval.decision == 'approved'",
                "rejected": "final_approval.decision == 'rejected'",
            },
        )

        # Store templates
        self.workflow_templates = {
            trade_processing.workflow_id: trade_processing,
            exception_handling.workflow_id: exception_handling,
            client_onboarding.workflow_id: client_onboarding,
        }

    async def execute_workflow(
        self,
        workflow_config: WorkflowConfig,
        input_data: Dict[str, Any],
        user_id: str,
        execution_options: Optional[Dict[str, Any]] = None,
    ) -> WorkflowExecutionResult:
        """
        Execute a workflow with the given configuration and input data

        Args:
            workflow_config: Workflow configuration
            input_data: Input data for the workflow
            user_id: User executing the workflow
            execution_options: Optional execution parameters

        Returns:
            WorkflowExecutionResult: Complete execution results
        """
        execution_id: str = str(uuid.uuid4())
        start_time = datetime.now()

        logger.info(
            f"Starting workflow execution: {workflow_config.workflow_id} [{execution_id}]"
        )

        # Initialize execution result
        execution_result = WorkflowExecutionResult(
            workflow_id=workflow_config.workflow_id,
            execution_id=execution_id,
            status=WorkflowStatus.RUNNING,
            start_time=start_time,
            end_time=None,
            total_execution_time_ms=0,
            node_results=[],
            final_output={},
            summary={},
        )

        # Store active execution
        self.active_executions[execution_id] = execution_result

        try:
            # Execute workflow based on type
            if workflow_config.workflow_type == WorkflowType.SEQUENTIAL:
                await self._execute_sequential_workflow(
                    workflow_config, input_data, execution_result
                )
            elif workflow_config.workflow_type == WorkflowType.PARALLEL:
                await self._execute_parallel_workflow(
                    workflow_config, input_data, execution_result
                )
            elif workflow_config.workflow_type == WorkflowType.HYBRID:
                await self._execute_hybrid_workflow(
                    workflow_config, input_data, execution_result
                )
            else:
                raise ValueError(
                    f"Unsupported workflow type: {workflow_config.workflow_type}"
                )

            # Mark as completed
            execution_result.status = WorkflowStatus.COMPLETED
            execution_result.end_time = datetime.now()
            execution_result.total_execution_time_ms = (
                execution_result.end_time - execution_result.start_time
            ).total_seconds() * 1000

            # Generate summary
            execution_result.summary = self._generate_execution_summary(
                execution_result
            )

            logger.info(f"Workflow execution completed: {execution_id}")

        except Exception as e:
            logger.error(f"Workflow execution failed: {execution_id} - {str(e)}")

            execution_result.status = WorkflowStatus.FAILED
            execution_result.end_time = datetime.now()
            execution_result.error_message = str(e)
            execution_result.total_execution_time_ms = (
                execution_result.end_time - execution_result.start_time
            ).total_seconds() * 1000

        return execution_result

    async def _execute_sequential_workflow(
        self,
        config: WorkflowConfig,
        input_data: Dict[str, Any],
        execution_result: WorkflowExecutionResult,
    ):
        """Execute nodes sequentially based on dependencies"""

        current_data = input_data.copy()
        executed_nodes = set()

        # Find entry point


        while current_node_id:
            node_config = next(
                (n for n in config.nodes if n.node_id == current_node_id), None
            )
            if not node_config:
                break

            # Check dependencies
            if node_config.dependencies:
                missing_deps = [
                    dep for dep in node_config.dependencies if dep not in executed_nodes
                ]
                if missing_deps:

                    logger.warning(
                        f"Missing dependencies for node {current_node_id}: {missing_deps}"
                    )
                    break

            # Execute node
            node_result = await self._execute_node(node_config, current_data)
            execution_result.node_results.append(node_result)

            executed_nodes.add(next_node_id)
            # Update current data with node output
            current_data.update(node_result.output_data)

            # Check if node failed and should stop execution
            if node_result.status == NodeExecutionStatus.FAILED:

                raise Exception(
                    f"Node {current_node_id} failed: {node_result.error_message}"
                )

                raise Exception(f"Node {next_node_id} failed: {node_result.error_message}")
            
            # Find next node (simplified - just execute all in order for now)

            remaining_nodes = [
                n for n in config.nodes if n.node_id not in executed_nodes
            ]
            current_node_id = remaining_nodes[0].node_id if remaining_nodes else None


        execution_result.final_output = current_data

    async def _execute_parallel_workflow(
        self,
        config: WorkflowConfig,
        input_data: Dict[str, Any],
        execution_result: WorkflowExecutionResult,
    ):
        """Execute nodes in parallel where possible"""

        # For now, implement simplified parallel execution
        # In production, this would use more sophisticated dependency resolution

        parallel_nodes = [n for n in config.nodes if not n.dependencies]
        sequential_nodes = [n for n in config.nodes if n.dependencies]

        # Execute parallel nodes
        if parallel_nodes:
            parallel_tasks = [
                self._execute_node(node_config, input_data)
                for node_config in parallel_nodes
            ]
            parallel_results = await asyncio.gather(*parallel_tasks)
            execution_result.node_results.extend(parallel_results)

        # Execute sequential nodes
        current_data = input_data.copy()
        for node_result in execution_result.node_results:
            current_data.update(node_result.output_data)

        for node_config in sequential_nodes:
            node_result = await self._execute_node(node_config, current_data)
            execution_result.node_results.append(node_result)
            current_data.update(node_result.output_data)

        execution_result.final_output = current_data

    async def _execute_hybrid_workflow(
        self,
        config: WorkflowConfig,
        input_data: Dict[str, Any],
        execution_result: WorkflowExecutionResult,
    ):
        """Execute hybrid workflow with both rules and agents"""

        # For now, treat as sequential - can be enhanced for more complex routing
        await self._execute_sequential_workflow(config, input_data, execution_result)

    async def _execute_node(
        self, node_config: WorkflowNodeConfig, input_data: Dict[str, Any]
    ) -> NodeExecutionResult:
        """Execute a single workflow node"""

        start_time = datetime.now()

        logger.info(f"Executing node: {node_config.node_id} ({node_config.node_type})")

        node_result = NodeExecutionResult(
            node_id=node_config.node_id,
            node_type=node_config.node_type,
            status=NodeExecutionStatus.RUNNING,
            start_time=start_time,
            end_time=None,
            execution_time_ms=0,
            input_data=input_data,
            output_data={},
            alerts=[],
            metadata={},
        )

        try:
            # Execute based on node type
            if node_config.node_type == "RULES_ENGINE":
                await self._execute_rules_engine_node(
                    node_config, input_data, node_result
                )
            elif node_config.node_type == "AGENT":
                await self._execute_agent_node(node_config, input_data, node_result)
            elif node_config.node_type == "DECISION":
                await self._execute_decision_node(node_config, input_data, node_result)
            elif node_config.node_type == "TRANSFORM":
                await self._execute_transform_node(node_config, input_data, node_result)
            else:
                raise ValueError(f"Unsupported node type: {node_config.node_type}")

            node_result.status = NodeExecutionStatus.COMPLETED

        except Exception as e:
            logger.error(f"Node execution failed: {node_config.node_id} - {str(e)}")
            node_result.status = NodeExecutionStatus.FAILED
            node_result.error_message = str(e)

        # Finalize timing
        node_result.end_time = datetime.now()
        node_result.execution_time_ms = (
            node_result.end_time - node_result.start_time
        ).total_seconds() * 1000

        return node_result

    async def _execute_rules_engine_node(
        self,
        node_config: WorkflowNodeConfig,
        input_data: Dict[str, Any],
        node_result: NodeExecutionResult,
    ):
        """Execute a rules engine node using Drools"""

        rule_sets = node_config.config.get("rule_sets", [])
        timeout_seconds = node_config.config.get("timeout_seconds", 30)

        # Extract trade data for rules
        trade_data = input_data.get("trade_data", input_data)

        # Create rule facts
        from app.services.drools_service import RuleFact

        facts = [
            RuleFact(
                fact_type="Trade",
                fact_id=trade_data.get("tradeId", "unknown"),
                data=trade_data,
                timestamp=datetime.now(),
            )
        ]

        # Add portfolio and client data if available
        if "portfolio_data" in input_data:
            facts.append(
                RuleFact(
                    fact_type="Portfolio",
                    fact_id=trade_data.get("portfolio", "unknown"),
                    data=input_data["portfolio_data"],
                    timestamp=datetime.now(),
                )
            )

        if "client_data" in input_data:
            facts.append(
                RuleFact(
                    fact_type="Client",
                    fact_id=trade_data.get("counterpartyId", "unknown"),
                    data=input_data["client_data"],
                    timestamp=datetime.now(),
                )
            )

        # Execute rules for each rule set
        all_results = []
        all_alerts = []

        async with self.drools_service:
            for rule_set in rule_sets:
                result = await self.drools_service.execute_rules(
                    rule_set=rule_set, facts=facts, timeout_seconds=timeout_seconds
                )
                all_results.append(result.to_dict())
                all_alerts.extend(result.actions_triggered)

        # Determine overall status
        validation_passed = not any(
            alert.get("type") in ["ValidationError", "RiskAlert", "ComplianceAlert"]
            and alert.get("severity") in ["HIGH", "CRITICAL"]
            for alert in all_alerts
        )

        node_result.output_data = {
            f"{node_config.node_id}_results": all_results,
            f"{node_config.node_id}_passed": validation_passed,
            "alerts": all_alerts,
            "rules_executed": len(rule_sets),
            "total_rules_fired": sum(
                len(r.get("rules_fired", [])) for r in all_results
            ),
        }

        node_result.alerts = all_alerts
        node_result.metadata = {
            "rule_sets_executed": rule_sets,
            "facts_processed": len(facts),
        }

    async def _execute_agent_node(
        self,
        node_config: WorkflowNodeConfig,
        input_data: Dict[str, Any],
        node_result: NodeExecutionResult,
    ):
        """Execute an AI agent node (mock implementation)"""

        agent_type = node_config.config.get("agent_type", "generic")

        # Mock agent execution for different types
        if agent_type == "document_generator":
            node_result.output_data = {
                f"{node_config.node_id}_generated": True,
                "documents": ["trade_confirmation.pdf"],
                "generation_method": "AI",
            }
        elif agent_type == "classifier":
            node_result.output_data = {
                f"{node_config.node_id}_classification": "data_quality",
                "confidence": 0.95,
                "reasoning": "Missing settlement date field",
            }
        elif agent_type == "advisor":
            node_result.output_data = {
                f"{node_config.node_id}_suggestions": [
                    "Update settlement date to next business day",
                    "Verify counterparty information",
                    "Request manual approval for large amount",
                ],
                "priority": "high",
            }
        else:
            node_result.output_data = {
                f"{node_config.node_id}_result": "completed",
                "agent_type": agent_type,
            }

        # Simulate processing time
        await asyncio.sleep(0.1)

    async def _execute_decision_node(
        self,
        node_config: WorkflowNodeConfig,
        input_data: Dict[str, Any],
        node_result: NodeExecutionResult,
    ):
        """Execute a decision node"""

        decision_logic = node_config.config.get("decision_logic", "True")

        # Simple decision evaluation (in production, use a proper expression evaluator)
        try:
            # For demo, make simple decisions based on data
            if "requires_manual_review" in decision_logic:
                decision = not input_data.get("auto_resolvable", False)
            else:
                decision = True

            node_result.output_data = {
                f"{node_config.node_id}_decision": (
                    "approved" if decision else "rejected"
                ),
                "decision_logic": decision_logic,
                "decision_value": decision,
            }
        except Exception as e:
            node_result.output_data = {
                f"{node_config.node_id}_decision": "error",
                "error": str(e),
            }

    async def _execute_transform_node(
        self,
        node_config: WorkflowNodeConfig,
        input_data: Dict[str, Any],
        node_result: NodeExecutionResult,
    ):
        """Execute a data transformation node"""

        transformations = node_config.config.get("transformations", {})

        transformed_data = input_data.copy()

        # Apply transformations
        for field, transformation in transformations.items():
            if transformation == "uppercase":
                if field in transformed_data:
                    transformed_data[field] = str(transformed_data[field]).upper()
            elif transformation == "format_currency":
                if field in transformed_data:
                    transformed_data[field] = f"${float(transformed_data[field]):,.2f}"

        node_result.output_data = {
            f"{node_config.node_id}_transformed": transformed_data,
            "transformations_applied": list(transformations.keys()),
        }

    def _generate_execution_summary(
        self, execution_result: WorkflowExecutionResult
    ) -> Dict[str, Any]:
        """Generate execution summary"""

        total_nodes = len(execution_result.node_results)
        completed_nodes = sum(
            1
            for nr in execution_result.node_results
            if nr.status == NodeExecutionStatus.COMPLETED
        )
        failed_nodes = sum(
            1
            for nr in execution_result.node_results
            if nr.status == NodeExecutionStatus.FAILED
        )

        total_alerts = sum(len(nr.alerts or []) for nr in execution_result.node_results)

        return {
            "total_nodes": total_nodes,
            "completed_nodes": completed_nodes,
            "failed_nodes": failed_nodes,
            "success_rate": completed_nodes / total_nodes if total_nodes > 0 else 0,
            "total_alerts": total_alerts,
            "execution_time_ms": execution_result.total_execution_time_ms,
            "workflow_type": execution_result.workflow_id,
            "final_status": execution_result.status.value,
        }

    def get_workflow_templates(self) -> Dict[str, WorkflowConfig]:
        """Get all available workflow templates"""
        return self.workflow_templates

    def get_active_executions(self) -> Dict[str, WorkflowExecutionResult]:
        """Get all currently active workflow executions"""
        return {
            exec_id: result
            for exec_id, result in self.active_executions.items()
            if result.status == WorkflowStatus.RUNNING
        }

    async def get_execution_status(
        self, execution_id: str
    ) -> Optional[WorkflowExecutionResult]:
        """Get status of a specific workflow execution"""
        return self.active_executions.get(execution_id)


# Singleton instance
_workflow_execution_service = None


def get_workflow_execution_service() -> WorkflowExecutionService:
    """Get singleton WorkflowExecutionService instance"""
    global _workflow_execution_service
    if _workflow_execution_service is None:
        _workflow_execution_service = WorkflowExecutionService()
    return _workflow_execution_service
