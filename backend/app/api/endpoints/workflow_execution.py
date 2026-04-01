"""
Workflow Execution API Endpoints for Otomeshon Custodian Portal

Provides REST API endpoints for configuring, executing, and monitoring
workflows that combine Drools rules engine with LangGraph agent workflows
for comprehensive custodian banking automation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.endpoints.auth_unified import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.workflow_execution_service import (
    WorkflowConfig,
    WorkflowExecutionResult,
    WorkflowExecutionService,
    WorkflowNodeConfig,
    WorkflowType,
    get_workflow_execution_service,
)

router = APIRouter(prefix="/workflow-execution", tags=["Workflow Execution"])

# Pydantic models for request/response


class WorkflowNodeConfigRequest(BaseModel):
    """Request model for workflow node configuration"""

    node_id: str = Field(..., description="Unique node identifier")
    node_type: str = Field(
        ..., description="Type of node (RULES_ENGINE, AGENT, DECISION, etc.)"
    )
    name: str = Field(..., description="Human-readable node name")
    description: str = Field(..., description="Node description")
    config: Dict[str, Any] = Field(..., description="Node-specific configuration")
    dependencies: Optional[List[str]] = Field(
        default=None, description="List of dependent node IDs"
    )
    conditions: Optional[Dict[str, Any]] = Field(
        default=None, description="Execution conditions"
    )
    timeout_seconds: int = Field(default=300, description="Node timeout in seconds")
    retry_count: int = Field(default=3, description="Number of retries on failure")


class WorkflowConfigRequest(BaseModel):
    """Request model for workflow configuration"""

    workflow_id: str = Field(..., description="Unique workflow identifier")
    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="Workflow description")
    workflow_type: WorkflowType = Field(..., description="Type of workflow")
    nodes: List[WorkflowNodeConfigRequest] = Field(
        ..., description="List of workflow nodes"
    )
    entry_point: str = Field(..., description="Entry point node ID")
    exit_conditions: Dict[str, Any] = Field(..., description="Exit conditions")
    global_timeout_seconds: int = Field(
        default=3600, description="Global workflow timeout"
    )
    enable_monitoring: bool = Field(
        default=True, description="Enable execution monitoring"
    )
    enable_audit: bool = Field(default=True, description="Enable audit logging")


class WorkflowExecutionRequest(BaseModel):
    """Request model for workflow execution"""

    workflow_id: str = Field(..., description="ID of workflow to execute")
    input_data: Dict[str, Any] = Field(..., description="Input data for workflow")
    execution_options: Optional[Dict[str, Any]] = Field(
        default=None, description="Execution options"
    )


class WorkflowExecutionResponse(BaseModel):
    """Response model for workflow execution"""

    execution_id: str
    workflow_id: str
    status: str
    start_time: str
    end_time: Optional[str]
    total_execution_time_ms: float
    node_results: List[Dict[str, Any]]
    final_output: Dict[str, Any]
    summary: Dict[str, Any]
    error_message: Optional[str] = None


class WorkflowTemplateResponse(BaseModel):
    """Response model for workflow templates"""

    workflow_id: str
    name: str
    description: str
    workflow_type: str
    nodes: List[Dict[str, Any]]
    entry_point: str
    exit_conditions: Dict[str, Any]


@router.get("/templates", response_model=List[WorkflowTemplateResponse])
async def get_workflow_templates(
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowExecutionService = Depends(
        get_workflow_execution_service
    ),
):
    """
    Get all available workflow templates

    Returns:
        List[WorkflowTemplateResponse]: Available workflow templates
    """
    try:
        templates = workflow_service.get_workflow_templates()

        return [
            WorkflowTemplateResponse(
                workflow_id=template.workflow_id,
                name=template.name,
                description=template.description,
                workflow_type=template.workflow_type.value,
                nodes=[node.to_dict() for node in template.nodes],
                entry_point=template.entry_point,
                exit_conditions=template.exit_conditions,
            )
            for template in templates.values()
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow templates: {str(e)}",
        )


@router.get("/templates/{workflow_id}", response_model=WorkflowTemplateResponse)
async def get_workflow_template(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowExecutionService = Depends(
        get_workflow_execution_service
    ),
):
    """
    Get a specific workflow template

    Args:
        workflow_id: ID of the workflow template

    Returns:
        WorkflowTemplateResponse: Workflow template details
    """
    try:
        templates = workflow_service.get_workflow_templates()
        template = templates.get(workflow_id)

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow template {workflow_id} not found",
            )

        return WorkflowTemplateResponse(
            workflow_id=template.workflow_id,
            name=template.name,
            description=template.description,
            workflow_type=template.workflow_type.value,
            nodes=[node.to_dict() for node in template.nodes],
            entry_point=template.entry_point,
            exit_conditions=template.exit_conditions,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow template: {str(e)}",
        )


@router.post("/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowExecutionService = Depends(
        get_workflow_execution_service
    ),
):
    """
    Execute a workflow with the provided input data

    Args:
        request: Workflow execution request

    Returns:
        WorkflowExecutionResponse: Execution results
    """
    try:
        # Get workflow template
        templates = workflow_service.get_workflow_templates()
        workflow_config = templates.get(request.workflow_id)

        if not workflow_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {request.workflow_id} not found",
            )

        # Execute workflow
        execution_result = await workflow_service.execute_workflow(
            workflow_config=workflow_config,
            input_data=request.input_data,
            user_id=current_user.email,
            execution_options=request.execution_options,
        )

        return WorkflowExecutionResponse(
            execution_id=execution_result.execution_id,
            workflow_id=execution_result.workflow_id,
            status=execution_result.status.value,
            start_time=execution_result.start_time.isoformat(),
            end_time=(
                execution_result.end_time.isoformat()
                if execution_result.end_time
                else None
            ),
            total_execution_time_ms=execution_result.total_execution_time_ms,
            node_results=[nr.to_dict() for nr in execution_result.node_results],
            final_output=execution_result.final_output,
            summary=execution_result.summary,
            error_message=execution_result.error_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}",
        )


@router.post("/execute-trade-processing", response_model=WorkflowExecutionResponse)
async def execute_trade_processing_workflow(
    trade_data: Dict[str, Any],
    portfolio_data: Optional[Dict[str, Any]] = None,
    client_data: Optional[Dict[str, Any]] = None,
    settlement_data: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowExecutionService = Depends(
        get_workflow_execution_service
    ),
):
    """
    Execute the trade processing workflow with trade data

    Args:
        trade_data: Trade information
        portfolio_data: Portfolio information (optional)
        client_data: Client information (optional)
        settlement_data: Settlement information (optional)

    Returns:
        WorkflowExecutionResponse: Execution results
    """
    try:
        # Prepare input data
        input_data = {
            "trade_data": trade_data,
            "portfolio_data": portfolio_data or {},
            "client_data": client_data or {},
            "settlement_data": settlement_data or {},
        }

        # Get trade processing workflow
        templates = workflow_service.get_workflow_templates()
        workflow_config = templates.get("trade_processing_v1")

        if not workflow_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trade processing workflow not found",
            )

        # Execute workflow
        execution_result = await workflow_service.execute_workflow(
            workflow_config=workflow_config,
            input_data=input_data,
            user_id=current_user.email,
        )

        return WorkflowExecutionResponse(
            execution_id=execution_result.execution_id,
            workflow_id=execution_result.workflow_id,
            status=execution_result.status.value,
            start_time=execution_result.start_time.isoformat(),
            end_time=(
                execution_result.end_time.isoformat()
                if execution_result.end_time
                else None
            ),
            total_execution_time_ms=execution_result.total_execution_time_ms,
            node_results=[nr.to_dict() for nr in execution_result.node_results],
            final_output=execution_result.final_output,
            summary=execution_result.summary,
            error_message=execution_result.error_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trade processing workflow failed: {str(e)}",
        )


@router.post("/execute-exception-handling", response_model=WorkflowExecutionResponse)
async def execute_exception_handling_workflow(
    exception_data: Dict[str, Any],
    trade_data: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowExecutionService = Depends(
        get_workflow_execution_service
    ),
):
    """
    Execute the exception handling workflow

    Args:
        exception_data: Exception information
        trade_data: Related trade data (optional)

    Returns:
        WorkflowExecutionResponse: Execution results
    """
    try:
        # Prepare input data
        input_data = {"exception_data": exception_data, "trade_data": trade_data or {}}

        # Get exception handling workflow
        templates = workflow_service.get_workflow_templates()
        workflow_config = templates.get("exception_handling_v1")

        if not workflow_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exception handling workflow not found",
            )

        # Execute workflow
        execution_result = await workflow_service.execute_workflow(
            workflow_config=workflow_config,
            input_data=input_data,
            user_id=current_user.email,
        )

        return WorkflowExecutionResponse(
            execution_id=execution_result.execution_id,
            workflow_id=execution_result.workflow_id,
            status=execution_result.status.value,
            start_time=execution_result.start_time.isoformat(),
            end_time=(
                execution_result.end_time.isoformat()
                if execution_result.end_time
                else None
            ),
            total_execution_time_ms=execution_result.total_execution_time_ms,
            node_results=[nr.to_dict() for nr in execution_result.node_results],
            final_output=execution_result.final_output,
            summary=execution_result.summary,
            error_message=execution_result.error_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Exception handling workflow failed: {str(e)}",
        )


@router.get("/executions", response_model=List[Dict[str, Any]])
async def get_active_executions(
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowExecutionService = Depends(
        get_workflow_execution_service
    ),
):
    """
    Get all currently active workflow executions

    Returns:
        List[Dict]: Active workflow executions
    """
    try:
        active_executions = workflow_service.get_active_executions()

        return [
            {
                "execution_id": exec_id,
                "workflow_id": result.workflow_id,
                "status": result.status.value,
                "start_time": result.start_time.isoformat(),
                "duration_ms": (datetime.now() - result.start_time).total_seconds()
                * 1000,
                "nodes_completed": len(
                    [nr for nr in result.node_results if nr.status.value == "completed"]
                ),
                "total_nodes": len(result.node_results),
            }
            for exec_id, result in active_executions.items()
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active executions: {str(e)}",
        )


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution_status(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowExecutionService = Depends(
        get_workflow_execution_service
    ),
):
    """
    Get status of a specific workflow execution

    Args:
        execution_id: ID of the workflow execution

    Returns:
        WorkflowExecutionResponse: Execution status and results
    """
    try:
        execution_result = await workflow_service.get_execution_status(execution_id)

        if not execution_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow execution {execution_id} not found",
            )

        return WorkflowExecutionResponse(
            execution_id=execution_result.execution_id,
            workflow_id=execution_result.workflow_id,
            status=execution_result.status.value,
            start_time=execution_result.start_time.isoformat(),
            end_time=(
                execution_result.end_time.isoformat()
                if execution_result.end_time
                else None
            ),
            total_execution_time_ms=execution_result.total_execution_time_ms,
            node_results=[nr.to_dict() for nr in execution_result.node_results],
            final_output=execution_result.final_output,
            summary=execution_result.summary,
            error_message=execution_result.error_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution status: {str(e)}",
        )


@router.get("/node-types")
async def get_supported_node_types(current_user: User = Depends(get_current_user)):
    """
    Get all supported workflow node types and their configurations

    Returns:
        Dict: Supported node types with configuration schemas
    """
    try:
        node_types = {
            "RULES_ENGINE": {
                "name": "Rules Engine",
                "description": "Execute Drools business rules",
                "config_schema": {
                    "rule_sets": {
                        "type": "array",
                        "description": "List of rule sets to execute",
                        "items": {"type": "string"},
                        "examples": [
                            "trade-validation",
                            "risk-management",
                            "compliance-checks",
                        ],
                    },
                    "timeout_seconds": {
                        "type": "integer",
                        "description": "Execution timeout in seconds",
                        "default": 30,
                    },
                    "require_all_passed": {
                        "type": "boolean",
                        "description": "Require all rules to pass",
                        "default": True,
                    },
                },
            },
            "AGENT": {
                "name": "AI Agent",
                "description": "Execute AI-powered agent tasks",
                "config_schema": {
                    "agent_type": {
                        "type": "string",
                        "description": "Type of AI agent",
                        "enum": [
                            "document_generator",
                            "classifier",
                            "advisor",
                            "risk_assessor",
                        ],
                    },
                    "model": {
                        "type": "string",
                        "description": "AI model to use",
                        "default": "gpt-4",
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Model temperature",
                        "default": 0.1,
                    },
                },
            },
            "DECISION": {
                "name": "Decision Node",
                "description": "Make routing decisions based on data",
                "config_schema": {
                    "decision_logic": {
                        "type": "string",
                        "description": "Decision logic expression",
                        "examples": [
                            "input.risk_score > 0.8",
                            "all(validations_passed)",
                        ],
                    },
                    "default_decision": {
                        "type": "string",
                        "description": "Default decision if logic fails",
                        "default": "reject",
                    },
                },
            },
            "TRANSFORM": {
                "name": "Data Transform",
                "description": "Transform and manipulate data",
                "config_schema": {
                    "transformations": {
                        "type": "object",
                        "description": "Field transformations to apply",
                        "examples": {
                            "amount": "format_currency",
                            "status": "uppercase",
                        },
                    }
                },
            },
            "MCP_CALL": {
                "name": "MCP Service Call",
                "description": "Call external MCP server",
                "config_schema": {
                    "server_name": {
                        "type": "string",
                        "description": "Name of MCP server to call",
                    },
                    "method": {
                        "type": "string",
                        "description": "Method to call on the server",
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Parameters for the method call",
                    },
                },
            },
        }

        return {
            "node_types": node_types,
            "total_types": len(node_types),
            "supported_workflows": [
                "SEQUENTIAL",
                "PARALLEL",
                "HYBRID",
                "RULES_BASED",
                "AGENT_BASED",
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get node types: {str(e)}",
        )


@router.get("/examples")
async def get_workflow_examples(current_user: User = Depends(get_current_user)):
    """
    Get example workflow configurations and input data

    Returns:
        Dict: Example workflows and data
    """
    try:
        examples = {
            "trade_processing_example": {
                "workflow_id": "trade_processing_v1",
                "name": "Trade Processing Example",
                "sample_input": {
                    "trade_data": {
                        "tradeId": "TRADE_EXAMPLE_001",
                        "tradeType": "EQUITY",
                        "counterpartyId": "CLIENT_001",
                        "securityId": "AAPL",
                        "quantity": 1000,
                        "price": 150.50,
                        "tradeValue": 150500.00,
                        "currency": "USD",
                        "tradeDate": "2024-07-20",
                        "settlementDate": "2024-07-22",
                        "status": "PENDING",
                        "portfolio": "PORTFOLIO_001",
                        "custodyAccount": "CUSTODY_001",
                    },
                    "portfolio_data": {
                        "portfolioId": "PORTFOLIO_001",
                        "totalExposure": 5000000.00,
                        "exposureLimit": 10000000.00,
                        "concentrationLimit": 1000000.00,
                        "availableCash": 2000000.00,
                    },
                    "client_data": {
                        "clientId": "CLIENT_001",
                        "kycStatus": "APPROVED",
                        "amlRiskRating": "LOW",
                        "creditRating": "A",
                    },
                },
                "expected_outcome": "Trade processed successfully through all validation steps",
            },
            "exception_handling_example": {
                "workflow_id": "exception_handling_v1",
                "name": "Exception Handling Example",
                "sample_input": {
                    "exception_data": {
                        "exceptionId": "EXC_001",
                        "exceptionType": "VALIDATION_ERROR",
                        "severity": "HIGH",
                        "description": "Invalid settlement date",
                        "tradeId": "TRADE_001",
                        "detectedAt": "2024-07-20T10:30:00Z",
                    },
                    "trade_data": {
                        "tradeId": "TRADE_001",
                        "settlementDate": "2024-07-18",
                        "tradeDate": "2024-07-20",
                    },
                },
                "expected_outcome": "Exception classified and resolution suggestions provided",
            },
        }

        return {
            "examples": examples,
            "usage_instructions": {
                "step1": "Choose a workflow template from /templates endpoint",
                "step2": "Prepare input data according to the example format",
                "step3": "Execute workflow using /execute endpoint",
                "step4": "Monitor execution using /executions/{execution_id} endpoint",
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow examples: {str(e)}",
        )
