from fastapi import APIRouter

from app.api.endpoints import (
    auth_unified,
    custodian_langgraph,
    data_sandbox,
    data_sources,
    data_streams,
    data_workflows,
    fibo,
    knowledge_graph,
    mcp_servers,
    rag,
    rag_findings,
    rules,
    sop_management,
    workflow_execution,
    workflows,
)

api_router = APIRouter()

# Core Business Logic Routers (these have their own prefixes defined)
# Authentication router - already has prefix="/auth"
api_router.include_router(auth_unified.router, tags=["Authentication"])

# Rules engine router - already has prefix="/rules"
api_router.include_router(rules.router, tags=["Rules Engine"])

# Workflow execution router - already has prefix="/workflow-execution"
api_router.include_router(workflow_execution.router, tags=["Workflow Execution"])

# SOP management router - already has prefix="/sop-management"
api_router.include_router(sop_management.router, tags=["SOP Management"])

# Additional Feature Routers (these need prefixes defined here)
api_router.include_router(
    mcp_servers.router, prefix="/mcp-servers", tags=["MCP Servers"]
)

api_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])

api_router.include_router(
    data_streams.router, prefix="/data-streams", tags=["Data Streams"]
)

api_router.include_router(data_sources.router, tags=["Data Sources"])

api_router.include_router(data_workflows.router, tags=["Data Workflows"])

api_router.include_router(
    knowledge_graph.router, prefix="/knowledge-graph", tags=["Knowledge Graph"]
)

api_router.include_router(
    data_sandbox.router, prefix="/data-sandbox", tags=["Data Sandbox"]
)

api_router.include_router(fibo.router, prefix="/fibo", tags=["FIBO Ontology"])


api_router.include_router(
    custodian_langgraph.router, tags=["Custodian LangGraph"]
)

api_router.include_router(rag.router, prefix="/rag", tags=["RAG Pipeline"])
api_router.include_router(
    rag_findings.router, prefix="/rag", tags=["RAG Findings (NAV)"]
)
