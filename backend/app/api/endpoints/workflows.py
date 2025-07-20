from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.models.workflow import Workflow, WorkflowNode, WorkflowEdge, WorkflowTrigger, WorkflowExecution

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
    status: Optional[str] = None,
    enabled_only: bool = False
):
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
async def create_workflow(workflow_data: WorkflowCreateRequest):
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
        "execution_settings": workflow_data.execution_settings or {
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
            }
        },
        "enabled": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_executed": None
    }
    
    workflows_db[workflow_id] = workflow
    return workflow

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str):
    """Get a specific workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflows_db[workflow_id]

@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: str, update_data: WorkflowUpdateRequest):
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
    
    return workflow

@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    del workflows_db[workflow_id]
    return {"message": "Workflow deleted successfully"}

@router.post("/{workflow_id}/activate")
async def activate_workflow(workflow_id: str):
    """Activate a workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflows_db[workflow_id]
    workflow["status"] = "ACTIVE"
    workflow["enabled"] = True
    workflow["updated_at"] = datetime.utcnow()
    
    return {"message": "Workflow activated successfully"}

@router.post("/{workflow_id}/deactivate")
async def deactivate_workflow(workflow_id: str):
    """Deactivate a workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflows_db[workflow_id]
    workflow["status"] = "PAUSED"
    workflow["enabled"] = False
    workflow["updated_at"] = datetime.utcnow()
    
    return {"message": "Workflow deactivated successfully"}

@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(workflow_id: str, execution_request: WorkflowExecutionRequest):
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
        "execution_steps": []
    }
    
    executions_db[execution_id] = execution
    
    # Update workflow last_executed
    workflow["last_executed"] = datetime.utcnow()
    
    # TODO: Implement actual workflow execution logic
    # For now, simulate execution
    execution["status"] = "RUNNING"
    
    return execution

@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecutionResponse])
async def list_workflow_executions(
    workflow_id: str,
    status: Optional[str] = None,
    limit: int = 50
):
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
    return executions[:limit]

@router.get("/{workflow_id}/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_workflow_execution(workflow_id: str, execution_id: str):
    """Get details of a specific workflow execution."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if execution_id not in executions_db:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    execution = executions_db[execution_id]
    if execution["workflow_id"] != workflow_id:
        raise HTTPException(status_code=404, detail="Execution not found for this workflow")
    
    return execution

@router.post("/{workflow_id}/executions/{execution_id}/cancel")
async def cancel_workflow_execution(workflow_id: str, execution_id: str):
    """Cancel a running workflow execution."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if execution_id not in executions_db:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    execution = executions_db[execution_id]
    if execution["workflow_id"] != workflow_id:
        raise HTTPException(status_code=404, detail="Execution not found for this workflow")
    
    if execution["status"] not in ["PENDING", "RUNNING"]:
        raise HTTPException(status_code=400, detail="Cannot cancel execution in current status")
    
    execution["status"] = "CANCELLED"
    execution["completed_at"] = datetime.utcnow()
    
    return {"message": "Workflow execution cancelled successfully"}

@router.get("/{workflow_id}/validate")
async def validate_workflow(workflow_id: str):
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
                validation_errors.append(f"Node {node['id']} missing MCP server configuration")
    
    return {
        "valid": len(validation_errors) == 0,
        "errors": validation_errors,
        "warnings": [],
        "workflow_id": workflow_id
    }