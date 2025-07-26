from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.services.mcp_service import MCPService, get_mcp_service

router = APIRouter()


# Request/Response Models
class MCPServerCreate(BaseModel):
    name: str
    provider_type: str  # CUSTODIAN, MARKET_DATA, OTHER
    base_url: str
    auth_type: str  # API_KEY, OAUTH, CERTIFICATE, BASIC
    auth_config: dict
    capabilities: List[str]
    description: Optional[str] = None


class MCPServerUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    auth_config: Optional[dict] = None
    capabilities: Optional[List[str]] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


class MCPServerResponse(BaseModel):
    id: str
    name: str
    provider_type: str
    base_url: str
    auth_type: str
    capabilities: List[str]
    description: Optional[str]
    status: str  # CONNECTED, DISCONNECTED, ERROR, TESTING
    enabled: bool
    last_ping: Optional[datetime]
    response_time_ms: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime


class MCPServerTestResult(BaseModel):
    server_id: str
    success: bool
    response_time_ms: int
    error_message: Optional[str]
    capabilities_discovered: List[str]
    tested_at: datetime


class MCPServerMetrics(BaseModel):
    server_id: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time_ms: float
    last_24h_requests: int
    uptime_percentage: float


@router.get("/", response_model=List[MCPServerResponse])
async def list_mcp_servers(
    provider_type: Optional[str] = None,
    enabled_only: bool = False,
    mcp_service: MCPService = Depends(get_mcp_service),
) -> List[MCPServerResponse]:
    """List all registered MCP servers."""
    servers = await mcp_service.list_servers(
        provider_type=provider_type, enabled_only=enabled_only
    )
    return [MCPServerResponse(**server) for server in servers]


@router.post("/", response_model=MCPServerResponse)
async def create_mcp_server(
    server_data: MCPServerCreate, mcp_service: MCPService = Depends(get_mcp_service)
) -> MCPServerResponse:
    """Register a new MCP server."""
    try:
        server = await mcp_service.create_server(server_data.dict())
        return MCPServerResponse(**server)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{server_id}", response_model=MCPServerResponse)
async def get_mcp_server(
    server_id: str, mcp_service: MCPService = Depends(get_mcp_service)
) -> MCPServerResponse:
    """Get details of a specific MCP server."""
    server = await mcp_service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return MCPServerResponse(**server)


@router.put("/{server_id}", response_model=MCPServerResponse)
async def update_mcp_server(
    server_id: str,
    update_data: MCPServerUpdate,
    mcp_service: MCPService = Depends(get_mcp_service),
) -> MCPServerResponse:
    """Update an MCP server configuration."""
    try:
        server = await mcp_service.update_server(
            server_id, update_data.dict(exclude_unset=True)
        )
        if not server:
            raise HTTPException(status_code=404, detail="MCP server not found")
        return MCPServerResponse(**server)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{server_id}")
async def delete_mcp_server(
    server_id: str, mcp_service: MCPService = Depends(get_mcp_service)
) -> Dict[str, str]:
    """Delete an MCP server."""
    success = await mcp_service.delete_server(server_id)
    if not success:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return {"message": "MCP server deleted successfully"}


@router.post("/{server_id}/test", response_model=MCPServerTestResult)
async def test_mcp_server(
    server_id: str, mcp_service: MCPService = Depends(get_mcp_service)
) -> MCPServerTestResult:
    """Test connection to an MCP server."""
    try:
        result = await mcp_service.test_server_connection(server_id)
        return MCPServerTestResult(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{server_id}/enable")
async def enable_mcp_server(
    server_id: str, mcp_service: MCPService = Depends(get_mcp_service)
) -> Dict[str, str]:
    """Enable an MCP server."""
    success = await mcp_service.enable_server(server_id)
    if not success:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return {"message": "MCP server enabled successfully"}


@router.post("/{server_id}/disable")
async def disable_mcp_server(
    server_id: str, mcp_service: MCPService = Depends(get_mcp_service)
) -> Dict[str, str]:
    """Disable an MCP server."""
    success = await mcp_service.disable_server(server_id)
    if not success:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return {"message": "MCP server disabled successfully"}


@router.get("/{server_id}/capabilities")
async def get_server_capabilities(
    server_id: str, mcp_service: MCPService = Depends(get_mcp_service)
) -> Dict[str, Any]:
    """Get available tools/capabilities from an MCP server."""
    try:
        capabilities = await mcp_service.get_server_capabilities(server_id)
        return {"server_id": server_id, "capabilities": capabilities}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{server_id}/metrics", response_model=MCPServerMetrics)
async def get_server_metrics(
    server_id: str, mcp_service: MCPService = Depends(get_mcp_service)
) -> MCPServerMetrics:
    """Get performance metrics for an MCP server."""
    try:
        metrics = await mcp_service.get_server_metrics(server_id)
        return MCPServerMetrics(**metrics)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{server_id}/call")
async def call_mcp_tool(
    server_id: str,
    tool_name: str,
    parameters: dict,
    mcp_service: MCPService = Depends(get_mcp_service),
) -> Dict[str, Any]:
    """Call a specific tool on an MCP server."""
    try:
        result = await mcp_service.call_tool(server_id, tool_name, parameters)
        return {
            "server_id": server_id,
            "tool_name": tool_name,
            "result": result,
            "timestamp": datetime.utcnow(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
