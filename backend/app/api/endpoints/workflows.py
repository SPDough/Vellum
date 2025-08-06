from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.models.workflow import WorkflowExecution
from app.services.langgraph_service import get_langgraph_service, LangGraphService
from app.services.langchain_service import get_langchain_service, LangchainService

router = APIRouter()


# Request/Response Models
class WorkflowCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    nodes: List[dict]
    edges: List[dict]
    triggers: List[dict] = []
    execution_settings: dict = {}


class WorkflowUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[dict]] = None
    edges: Optional[List[dict]] = None
    triggers: Optional[List[dict]] = None
    execution_settings: Optional[dict] = None
    enabled: Optional[bool] = None


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str  # DRAFT, ACTIVE, PAUSED, ERROR
    version: int
    nodes: List[dict]
    edges: List[dict]
    triggers: List[dict]
    execution_settings: dict
    enabled: bool
    created_at: datetime
    updated_at: datetime
    last_executed: Optional[datetime] = None


class WorkflowExecutionRequest(BaseModel):
    input_data: dict = {}
    trigger_type: str = "manual"


class WorkflowExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    status: str  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    trigger_type: str
    input_data: dict
    output_data: Optional[dict] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_steps: List[dict] = []


# Mock storage - replace with actual database
workflows_db: dict = {}
executions_db: dict = {}


@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    status: Optional[str] = None, enabled_only: bool = False
) -> List[WorkflowResponse]:
    """List all workflows."""
    workflows = []
    for workflow_id, workflow_data in workflows_db.items():
        if status and workflow_data.get("status") != status:
            continue
        if enabled_only and not workflow_data.get("enabled", True):
            continue
        workflows.append(workflow_data)

    # Sort by updated_at descending
    workflows.sort(key=lambda x: x.get("updated_at", datetime.min), reverse=True)
    return workflows


@router.post("/", response_model=WorkflowResponse)
async def create_workflow(workflow_data: WorkflowCreateRequest) -> WorkflowResponse:
    """Create a new workflow."""
    workflow_id = str(uuid4())

    workflow = {
        "id": workflow_id,
        "name": workflow_data.name,
        "description": workflow_data.description,
        "status": "DRAFT",
        "version": 1,
        "nodes": workflow_data.nodes,
        "edges": workflow_data.edges,
        "triggers": workflow_data.triggers,
        "execution_settings": workflow_data.execution_settings
        or {
            "max_concurrent_executions": 1,
            "execution_timeout_minutes": 60,
            "retry_policy": {
                "max_attempts": 3,
                "backoff_strategy": "EXPONENTIAL",
                "delay_seconds": 30,
            },
            "notification_settings": {
                "on_success": False,
                "on_failure": True,
                "on_long_running": False,
                "recipients": [],
                "channels": [],
            },
        },
        "enabled": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_executed": None,
    }

    workflows_db[workflow_id] = workflow
    return WorkflowResponse(**workflow)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str) -> WorkflowResponse:
    """Get a specific workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return WorkflowResponse(**workflows_db[workflow_id])


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str, update_data: WorkflowUpdateRequest
) -> WorkflowResponse:
    """Update a workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = workflows_db[workflow_id]

    # Update fields if provided
    if update_data.name is not None:
        workflow["name"] = update_data.name
    if update_data.description is not None:
        workflow["description"] = update_data.description
    if update_data.nodes is not None:
        workflow["nodes"] = update_data.nodes
        workflow["version"] += 1  # Increment version on structural changes
    if update_data.edges is not None:
        workflow["edges"] = update_data.edges
        workflow["version"] += 1
    if update_data.triggers is not None:
        workflow["triggers"] = update_data.triggers
    if update_data.execution_settings is not None:
        workflow["execution_settings"] = update_data.execution_settings
    if update_data.enabled is not None:
        workflow["enabled"] = update_data.enabled

    workflow["updated_at"] = datetime.utcnow()

    return WorkflowResponse(**workflow)


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str) -> Dict[str, Any]:
    """Delete a workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")

    del workflows_db[workflow_id]
    return {"message": "Workflow deleted successfully"}


@router.post("/{workflow_id}/activate")
async def activate_workflow(workflow_id: str) -> Dict[str, Any]:
    """Activate a workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = workflows_db[workflow_id]
    workflow["status"] = "ACTIVE"
    workflow["enabled"] = True
    workflow["updated_at"] = datetime.utcnow()

    return {"message": "Workflow activated successfully"}


@router.post("/{workflow_id}/deactivate")
async def deactivate_workflow(workflow_id: str) -> Dict[str, Any]:
    """Deactivate a workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = workflows_db[workflow_id]
    workflow["status"] = "PAUSED"
    workflow["enabled"] = False
    workflow["updated_at"] = datetime.utcnow()

    return {"message": "Workflow deactivated successfully"}


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: str, execution_request: WorkflowExecutionRequest
) -> WorkflowExecutionResponse:
    """Execute a workflow manually."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = workflows_db[workflow_id]
    execution_id = str(uuid4())

    execution = {
        "id": execution_id,
        "workflow_id": workflow_id,
        "status": "PENDING",
        "trigger_type": execution_request.trigger_type,
        "input_data": execution_request.input_data,
        "output_data": None,
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "error_message": None,
        "execution_steps": [],
    }

    executions_db[execution_id] = execution

    # Update workflow last_executed
    workflow["last_executed"] = datetime.utcnow()

    # TODO: Implement actual workflow execution logic
    # For now, simulate execution
    execution["status"] = "RUNNING"

    return WorkflowExecutionResponse(**execution)


@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecutionResponse])
async def list_workflow_executions(
    workflow_id: str, status: Optional[str] = None, limit: int = 50
) -> List[WorkflowExecutionResponse]:
    """List executions for a specific workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")

    executions = []
    for execution_id, execution_data in executions_db.items():
        if execution_data["workflow_id"] != workflow_id:
            continue
        if status and execution_data.get("status") != status:
            continue
        executions.append(execution_data)

    # Sort by started_at descending and limit
    executions.sort(key=lambda x: x.get("started_at", datetime.min), reverse=True)
    return [WorkflowExecutionResponse(**execution) for execution in executions[:limit]]


@router.get(
    "/{workflow_id}/executions/{execution_id}", response_model=WorkflowExecutionResponse
)
async def get_workflow_execution(
    workflow_id: str, execution_id: str
) -> WorkflowExecutionResponse:
    """Get details of a specific workflow execution."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if execution_id not in executions_db:
        raise HTTPException(status_code=404, detail="Execution not found")

    execution = executions_db[execution_id]
    if execution["workflow_id"] != workflow_id:
        raise HTTPException(
            status_code=404, detail="Execution not found for this workflow"
        )

    return WorkflowExecutionResponse(**execution)


@router.post("/{workflow_id}/executions/{execution_id}/cancel")
async def cancel_workflow_execution(
    workflow_id: str, execution_id: str
) -> Dict[str, Any]:
    """Cancel a running workflow execution."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if execution_id not in executions_db:
        raise HTTPException(status_code=404, detail="Execution not found")

    execution = executions_db[execution_id]
    if execution["workflow_id"] != workflow_id:
        raise HTTPException(
            status_code=404, detail="Execution not found for this workflow"
        )

    if execution["status"] not in ["PENDING", "RUNNING"]:
        raise HTTPException(
            status_code=400, detail="Cannot cancel execution in current status"
        )

    execution["status"] = "CANCELLED"
    execution["completed_at"] = datetime.utcnow()

    return {"message": "Workflow execution cancelled successfully"}


@router.get("/{workflow_id}/validate")
async def validate_workflow(workflow_id: str) -> Dict[str, Any]:
    """Validate a workflow configuration."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = workflows_db[workflow_id]

    # Basic validation logic
    validation_errors = []

    # Check if workflow has nodes
    if not workflow.get("nodes"):
        validation_errors.append("Workflow must have at least one node")

    # Check for disconnected nodes
    node_ids = {node["id"] for node in workflow.get("nodes", [])}
    edge_nodes = set()
    for edge in workflow.get("edges", []):
        edge_nodes.add(edge.get("source"))
        edge_nodes.add(edge.get("target"))

    disconnected_nodes = node_ids - edge_nodes
    if len(disconnected_nodes) > 1:  # Allow one start node to be disconnected
        validation_errors.append(f"Disconnected nodes found: {disconnected_nodes}")

    # Check for valid MCP server references
    for node in workflow.get("nodes", []):
        if node.get("type") == "MCP_CALL":
            mcp_server_id = node.get("config", {}).get("mcp_server_id")
            if not mcp_server_id:
                validation_errors.append(
                    f"Node {node['id']} missing MCP server configuration"
                )

    return {
        "valid": len(validation_errors) == 0,
        "errors": validation_errors,
        "warnings": [],
        "workflow_id": workflow_id,
    }


# Langchain and Langgraph specific endpoints
@router.get("/langchain/list", response_model=List[Dict[str, Any]])
async def list_langchain_workflows(
    langchain_service: LangchainService = Depends(get_langchain_service)
) -> List[Dict[str, Any]]:
    """List all Langchain workflows."""
    return langchain_service.list_workflows()


@router.get("/langgraph/list", response_model=List[Dict[str, Any]])
async def list_langgraph_workflows(
    langgraph_service: LangGraphService = Depends(get_langgraph_service)
) -> List[Dict[str, Any]]:
    """List all Langgraph workflows."""
    return langgraph_service.list_workflows()


@router.post("/langchain/create/{template_type}")
async def create_langchain_workflow(
    template_type: str,
    langchain_service: LangchainService = Depends(get_langchain_service)
) -> Dict[str, Any]:
    """Create a new Langchain workflow from template."""
    try:
        if template_type == "position_analysis":
            workflow_id = await langchain_service.create_position_analysis_workflow()
        elif template_type == "trade_validation":
            workflow_id = await langchain_service.create_trade_validation_workflow()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown template type: {template_type}"
            )

        return {
            "workflow_id": workflow_id,
            "workflow_type": "LANGCHAIN",
            "template_type": template_type,
            "status": "CREATED"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/langgraph/create/{template_type}")
async def create_langgraph_workflow(
    template_type: str,
    langgraph_service: LangGraphService = Depends(get_langgraph_service)
) -> Dict[str, Any]:
    """Create a new Langgraph workflow from template."""
    try:
        if template_type == "fibo_mapping":
            workflow_id = await langgraph_service.create_fibo_mapping_workflow()
        elif template_type == "trade_validation":
            workflow_id = await langgraph_service.create_trade_validation_workflow()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown template type: {template_type}"
            )

        return {
            "workflow_id": workflow_id,
            "workflow_type": "LANGGRAPH",
            "template_type": template_type,
            "status": "CREATED"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/langchain/{workflow_id}/execute")
async def execute_langchain_workflow(
    workflow_id: str,
    execution_request: WorkflowExecutionRequest,
    langchain_service: LangchainService = Depends(get_langchain_service)
) -> Dict[str, Any]:
    """Execute a Langchain workflow."""
    try:
        result = await langchain_service.execute_workflow(
            workflow_id, execution_request.input_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/langgraph/{workflow_id}/execute")
async def execute_langgraph_workflow(
    workflow_id: str,
    execution_request: WorkflowExecutionRequest,
    langgraph_service: LangGraphService = Depends(get_langgraph_service)
) -> Dict[str, Any]:
    """Execute a Langgraph workflow."""
    try:
        result = await langgraph_service.execute_workflow(
            workflow_id, execution_request.input_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/langchain/{workflow_id}/info")
async def get_langchain_workflow_info(
    workflow_id: str,
    langchain_service: LangchainService = Depends(get_langchain_service)
) -> Dict[str, Any]:
    """Get information about a Langchain workflow."""
    workflow_info = await langchain_service.get_workflow_info(workflow_id)
    if not workflow_info:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow_info


@router.get("/langgraph/{workflow_id}/info")
async def get_langgraph_workflow_info(
    workflow_id: str,
    langgraph_service: LangGraphService = Depends(get_langgraph_service)
) -> Dict[str, Any]:
    """Get information about a Langgraph workflow."""
    workflow_info = await langgraph_service.get_workflow_info(workflow_id)
    if not workflow_info:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow_info


@router.get("/templates/langchain")
async def get_langchain_templates(
    langchain_service: LangchainService = Depends(get_langchain_service)
) -> List[Dict[str, Any]]:
    """Get available Langchain workflow templates."""
    return langchain_service.get_available_templates()


@router.get("/templates/langgraph")
async def get_langgraph_templates(
    langgraph_service: LangGraphService = Depends(get_langgraph_service)
) -> List[Dict[str, Any]]:
    """Get available Langgraph workflow templates."""
    return langgraph_service.get_available_nodes()


@router.get("/all/summary")
async def get_all_workflows_summary(
    langchain_service: LangchainService = Depends(get_langchain_service),
    langgraph_service: LangGraphService = Depends(get_langgraph_service)
) -> Dict[str, Any]:
    """Get summary of all workflow types."""
    langchain_workflows = langchain_service.list_workflows()
    langgraph_workflows = langgraph_service.list_workflows()
    standard_workflows = list(workflows_db.values())

    return {
        "summary": {
            "total_workflows": len(langchain_workflows) + len(langgraph_workflows) + len(standard_workflows),
            "langchain_count": len(langchain_workflows),
            "langgraph_count": len(langgraph_workflows),
            "standard_count": len(standard_workflows)
        },
        "langchain_workflows": langchain_workflows,
        "langgraph_workflows": langgraph_workflows,
        "standard_workflows": [
            {
                "workflow_id": w["id"],
                "name": w["name"],
                "status": w["status"],
                "workflow_type": "STANDARD"
            }
            for w in standard_workflows
        ],
        "templates": {
            "langchain": langchain_service.get_available_templates(),
            "langgraph": langgraph_service.get_available_nodes()
        }
    }
