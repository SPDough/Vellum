from fastapi import APIRouter

from app.api.endpoints import mcp_servers, workflows, data_streams, knowledge_graph, data_sandbox, rules, auth_unified, workflow_execution, sop_management

api_router = APIRouter()

# Include authentication router
api_router.include_router(
    auth_unified.router,
    tags=["Authentication"]
)

# Include rules engine router
api_router.include_router(
    rules.router,
    tags=["Rules Engine"]
)

# Include workflow execution router
api_router.include_router(
    workflow_execution.router,
    tags=["Workflow Execution"]
)

# Include SOP management router
api_router.include_router(
    sop_management.router,
    tags=["SOP Management"]
)

# Include all endpoint routers
api_router.include_router(
    mcp_servers.router,
    prefix="/mcp-servers",
    tags=["MCP Servers"]
)

api_router.include_router(
    workflows.router,
    prefix="/workflows",
    tags=["Workflows"]
)

api_router.include_router(
    data_streams.router,
    prefix="/data-streams",
    tags=["Data Streams"]
)

api_router.include_router(
    knowledge_graph.router,
    prefix="/knowledge-graph",
    tags=["Knowledge Graph"]
)

api_router.include_router(
    data_sandbox.router,
    prefix="/data-sandbox",
    tags=["Data Sandbox"]
)