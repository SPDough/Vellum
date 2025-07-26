from fastapi import APIRouter

from app.api.endpoints import (
    data_sandbox,
    data_streams,
    knowledge_graph,
    mcp_servers,
    workflows,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    mcp_servers.router, prefix="/mcp-servers", tags=["MCP Servers"]
)

api_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])

api_router.include_router(
    data_streams.router, prefix="/data-streams", tags=["Data Streams"]
)

api_router.include_router(
    knowledge_graph.router, prefix="/knowledge-graph", tags=["Knowledge Graph"]
)

api_router.include_router(
    data_sandbox.router, prefix="/data-sandbox", tags=["Data Sandbox"]
)
