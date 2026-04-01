"""
Custodian LangGraph API Endpoints

API endpoints for managing custodian data analysis workflows using LangGraph.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.services.custodian_langgraph_service import (
    CustodianLangGraphService,
    get_custodian_langgraph_service
)

router = APIRouter(prefix="/custodian-langgraph", tags=["custodian-langgraph"])


class CustodianWorkflowCreate(BaseModel):
    """Request model for creating custodian workflows."""
    custodian_name: str
    api_key: Optional[str] = None


class CustodianAnalysisRequest(BaseModel):
    """Request model for executing custodian analysis."""
    endpoint: str = "/positions"
    capability_id: Optional[str] = None  # e.g. "positions" — overrides endpoint when spec exists
    params: Optional[Dict[str, Any]] = None
    user_question: str = "Analyze this custodian data"


class CustodianConfigCreate(BaseModel):
    """Request model for adding custodian configurations."""
    name: str
    base_url: str
    auth_type: str = "bearer"
    api_key: Optional[str] = None


@router.post("/workflows/create")
async def create_custodian_workflow(
    request: CustodianWorkflowCreate,
    service: CustodianLangGraphService = Depends(get_custodian_langgraph_service)
) -> Dict[str, Any]:
    """Create a new custodian data analysis workflow."""
    try:
        workflow_id = await service.create_custodian_analysis_workflow(
            custodian_name=request.custodian_name,
            api_key=request.api_key
        )
        
        return {
            "workflow_id": workflow_id,
            "custodian_name": request.custodian_name,
            "status": "CREATED",
            "message": f"Workflow created for {request.custodian_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/{workflow_id}/execute")
async def execute_custodian_analysis(
    workflow_id: str,
    request: CustodianAnalysisRequest,
    service: CustodianLangGraphService = Depends(get_custodian_langgraph_service)
) -> Dict[str, Any]:
    """Execute a custodian data analysis workflow. Use capability_id for spec-backed custodians (e.g. state_street)."""
    try:
        result = await service.execute_custodian_analysis(
            workflow_id=workflow_id,
            endpoint=request.endpoint,
            capability_id=request.capability_id,
            params=request.params,
            user_question=request.user_question,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/custodians")
async def list_custodians(
    service: CustodianLangGraphService = Depends(get_custodian_langgraph_service)
) -> List[Dict[str, Any]]:
    """List available custodian configurations (includes capabilities for spec-backed custodians)."""
    try:
        return service.list_available_custodians()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/custodians/{custodian_id}/capabilities")
async def get_custodian_capabilities(
    custodian_id: str,
) -> Dict[str, Any]:
    """Get API capabilities for a custodian (e.g. State Street). Returns endpoints and auth info."""
    from app.services.custodian_apis import get_custodian_api_spec

    spec = get_custodian_api_spec(custodian_id)
    if not spec:
        raise HTTPException(
            status_code=404,
            detail=f"No API spec found for custodian: {custodian_id}",
        )
    out = {
        "custodian_id": spec.custodian_id,
        "display_name": spec.display_name,
        "base_url": spec.base_url,
        "auth_type": spec.auth_type,
        "version": spec.version,
        "capabilities": spec.to_capabilities_list(),
    }
    if getattr(spec, "source_document", None):
        out["source_document"] = spec.source_document
    return out


@router.post("/custodians")
async def add_custodian_config(
    request: CustodianConfigCreate,
    service: CustodianLangGraphService = Depends(get_custodian_langgraph_service)
) -> Dict[str, Any]:
    """Add a new custodian configuration."""
    try:
        service.add_custodian_config(
            name=request.name,
            base_url=request.base_url,
            auth_type=request.auth_type,
            api_key=request.api_key
        )
        
        return {
            "name": request.name,
            "base_url": request.base_url,
            "auth_type": request.auth_type,
            "status": "ADDED",
            "message": f"Custodian configuration added: {request.name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    service: CustodianLangGraphService = Depends(get_custodian_langgraph_service)
) -> Dict[str, Any]:
    """Get the status of a custodian workflow."""
    try:
        if workflow_id not in service.graphs:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "workflow_id": workflow_id,
            "status": "ACTIVE",
            "node_count": len(service.graphs[workflow_id].nodes),
            "message": "Workflow is active and ready for execution"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    service: CustodianLangGraphService = Depends(get_custodian_langgraph_service)
) -> Dict[str, Any]:
    """Delete a custodian workflow."""
    try:
        if workflow_id not in service.graphs:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        del service.graphs[workflow_id]
        service.workflow_custodian.pop(workflow_id, None)
        
        return {
            "workflow_id": workflow_id,
            "status": "DELETED",
            "message": "Workflow deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows")
async def list_workflows(
    service: CustodianLangGraphService = Depends(get_custodian_langgraph_service)
) -> Dict[str, Any]:
    """List all custodian workflows."""
    try:
        workflows = []
        for workflow_id, graph in service.graphs.items():
            workflows.append({
                "workflow_id": workflow_id,
                "node_count": len(graph.nodes),
                "status": "ACTIVE"
            })
        
        return {
            "workflows": workflows,
            "total_count": len(workflows)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
