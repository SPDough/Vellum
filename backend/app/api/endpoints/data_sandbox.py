import io
from typing import List, Optional


from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Response,
    WebSocket,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.models.data_sandbox import (
    AgentResult,
    AgentResultCreate,
    DataExportRequest,
    DataLineage,
    DataQualityAnalysis,
    DataQuery,
    DataQueryResult,
    DataSourceCreate,
    DataSourceResponse,
    DataSourceUpdate,
    DataVisualizationCreate,
    DataVisualizationResponse,
    MCPDataStream,
    MCPDataStreamCreate,
    WorkflowOutput,
    WorkflowOutputCreate,
)
from app.services.data_sandbox_service import (
    DataSandboxService,
    get_data_sandbox_service,
)
from app.services.websocket_service import connection_manager, data_stream_service

router = APIRouter()


# Data Sources
@router.post("/sources", response_model=DataSourceResponse)
async def create_data_source(
    data_source: DataSourceCreate,
    service: DataSandboxService = Depends(get_data_sandbox_service),
):
    """Create a new data source."""
    return await service.create_data_source(data_source)


@router.get("/sources", response_model=List[DataSourceResponse])
async def list_data_sources(
    service: DataSandboxService = Depends(get_data_sandbox_service),
):
    """List all data sources."""
    return await service.get_data_sources()


@router.get("/sources/{source_id}", response_model=DataSourceResponse)
async def get_data_source(
    source_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Get a specific data source."""
    data_source = await service.get_data_source(source_id)
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return data_source


@router.put("/sources/{source_id}", response_model=DataSourceResponse)
async def update_data_source(
    source_id: str,
    updates: DataSourceUpdate,
    service: DataSandboxService = Depends(get_data_sandbox_service),
):
    """Update a data source."""
    data_source = await service.update_data_source(source_id, updates)
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return data_source


@router.delete("/sources/{source_id}")
async def delete_data_source(
    source_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Delete a data source."""
    success = await service.delete_data_source(source_id)
    if not success:
        raise HTTPException(status_code=404, detail="Data source not found")
    return {"message": "Data source deleted successfully"}


@router.get("/sources/{source_id}/preview", response_model=DataQueryResult)
async def get_data_preview(
    source_id: str,
    limit: int = 100,
    service: DataSandboxService = Depends(get_data_sandbox_service),
):
    """Get a preview of data from a source."""
    data, total_count, execution_time = await service.get_data_preview(source_id, limit)
    data_source = await service.get_data_source(source_id)

    return DataQueryResult(
        data=data,
        total_count=total_count,
        schema=data_source.schema if data_source else None,
        execution_time=execution_time,
        source=data_source,
    )


# Data Querying
@router.post("/query", response_model=DataQueryResult)
async def query_data(
    query: DataQuery, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Execute a data query."""
    data, total_count, execution_time = await service.query_data(query)
    data_source = await service.get_data_source(query.source)

    return DataQueryResult(
        data=data,
        total_count=total_count,
        schema=data_source.schema if data_source else None,
        execution_time=execution_time,
        source=data_source,
    )


@router.post("/sql", response_model=DataQueryResult)
async def execute_sql(
    sql_request: dict, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Execute a SQL query."""
    # This would implement SQL query execution
    # For now, return a placeholder
    return DataQueryResult(
        data=[], total_count=0, schema=None, execution_time=0.0, source=None
    )


# Workflow Integration
@router.get("/workflow-outputs", response_model=List[WorkflowOutput])
async def get_workflow_outputs(
    workflow_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    step_name: Optional[str] = None,
    limit: Optional[int] = None,
    since: Optional[str] = None,
    service: DataSandboxService = Depends(get_data_sandbox_service),
):
    """Get workflow outputs."""
    # This would integrate with the workflow service
    # For now, return mock data
    return []


@router.get("/workflow-outputs/{output_id}", response_model=WorkflowOutput)
async def get_workflow_output(
    output_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Get a specific workflow output."""
    # This would integrate with the workflow service
    raise HTTPException(status_code=404, detail="Workflow output not found")


@router.post("/sources/from-workflow", response_model=DataSourceResponse)
async def create_data_source_from_workflow(
    request: dict, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Create a data source from workflow outputs."""
    workflow_id = request.get("workflow_id")
    output_name = request.get("output_name")

    if not workflow_id or not output_name:
        raise HTTPException(
            status_code=400, detail="workflow_id and output_name are required"
        )

    return await service.create_data_source_from_workflow(workflow_id, output_name)


# MCP Integration
@router.get("/mcp-streams", response_model=List[MCPDataStream])
async def get_mcp_data_streams(
    server_id: Optional[str] = None,
    stream_name: Optional[str] = None,
    limit: Optional[int] = None,
    since: Optional[str] = None,
    service: DataSandboxService = Depends(get_data_sandbox_service),
):
    """Get MCP data streams."""
    # This would integrate with the MCP service
    # For now, return mock data
    return []


@router.get("/mcp-streams/{stream_id}", response_model=MCPDataStream)
async def get_mcp_data_stream(
    stream_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Get a specific MCP data stream."""
    # This would integrate with the MCP service
    raise HTTPException(status_code=404, detail="MCP data stream not found")


@router.post("/sources/from-mcp", response_model=DataSourceResponse)
async def create_data_source_from_mcp(
    request: dict, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Create a data source from MCP stream."""
    server_id = request.get("server_id")
    stream_name = request.get("stream_name")

    if not server_id or not stream_name:
        raise HTTPException(
            status_code=400, detail="server_id and stream_name are required"
        )

    return await service.create_data_source_from_mcp(server_id, stream_name)


# Agent Integration
@router.get("/agent-results", response_model=List[AgentResult])
async def get_agent_results(
    agent_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: Optional[int] = None,
    since: Optional[str] = None,
    service: DataSandboxService = Depends(get_data_sandbox_service),
):
    """Get agent results."""
    # This would integrate with the agent service
    # For now, return mock data
    return []


@router.get("/agent-results/{result_id}", response_model=AgentResult)
async def get_agent_result(
    result_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Get a specific agent result."""
    # This would integrate with the agent service
    raise HTTPException(status_code=404, detail="Agent result not found")


@router.post("/sources/from-agent", response_model=DataSourceResponse)
async def create_data_source_from_agent(
    request: dict, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Create a data source from agent results."""
    agent_id = request.get("agent_id")
    task_type = request.get("task_type")

    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")

    # This would create a data source for agent results
    # For now, create a placeholder
    from app.models.data_sandbox import DataSourceCreate, DataSourceType

    data_source_create = DataSourceCreate(
        name=f"Agent Results: {agent_id}",
        type=DataSourceType.AGENT,
        description=f"Results from agent {agent_id}",
        source_metadata={"agent_id": agent_id, "task_type": task_type},
    )

    return await service.create_data_source(data_source_create)


# Data Export
@router.post("/export")
async def export_data(
    request: DataExportRequest,
    service: DataSandboxService = Depends(get_data_sandbox_service),
):
    """Export data in the specified format."""
    data_bytes = await service.export_data(
        request.query, request.format, request.filename
    )

    # Determine content type and filename
    if request.format == "csv":
        content_type = "text/csv"
        filename = request.filename or "export.csv"
    elif request.format == "json":
        content_type = "application/json"
        filename = request.filename or "export.json"
    elif request.format == "xlsx":
        content_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = request.filename or "export.xlsx"
    else:
        content_type = "application/octet-stream"
        filename = request.filename or "export.dat"

    return StreamingResponse(
        io.BytesIO(data_bytes),
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/scheduled-exports")
async def schedule_export(
    request: dict, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Schedule a recurring data export."""
    # This would implement scheduled exports
    # For now, return a placeholder
    return {"message": "Export scheduled successfully", "schedule_id": "schedule_123"}


# Data Transformation
@router.post("/sources/{source_id}/transform", response_model=DataQueryResult)
async def transform_data(
    source_id: str,
    request: dict,
    service: DataSandboxService = Depends(get_data_sandbox_service),
):
    """Transform data from a source."""
    # This would implement data transformation
    # For now, return the original data
    data, total_count, execution_time = await service.get_data_preview(source_id, 100)
    data_source = await service.get_data_source(source_id)

    return DataQueryResult(
        data=data,
        total_count=total_count,
        schema=data_source.schema if data_source else None,
        execution_time=execution_time,
        source=data_source,
    )


@router.post("/transformations", response_model=DataSourceResponse)
async def save_transformation(
    request: dict, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Save a data transformation as a new data source."""
    # This would create a new data source with transformed data
    # For now, return a placeholder
    from app.models.data_sandbox import DataSourceCreate, DataSourceType

    data_source_create = DataSourceCreate(
        name=request.get("name", "Transformed Data"),
        type=DataSourceType.MANUAL,
        description="Data source created from transformation",
        source_metadata={
            "source_id": request.get("source_id"),
            "transformations": request.get("transformations"),
        },
    )

    return await service.create_data_source(data_source_create)


# Visualizations
@router.post("/visualizations", response_model=DataVisualizationResponse)
async def save_visualization(
    config: DataVisualizationCreate,
    service: DataSandboxService = Depends(get_data_sandbox_service),
):
    """Save a data visualization configuration."""
    # This would save visualization config to database
    # For now, return a mock response
    from datetime import datetime

    return DataVisualizationResponse(
        id="viz_123",
        title=config.title,
        description=config.description,
        type=config.type,
        config=config.config,
        created_by="user_123",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@router.get("/visualizations", response_model=List[DataVisualizationResponse])
async def get_visualizations(
    service: DataSandboxService = Depends(get_data_sandbox_service),
):
    """Get all saved visualizations."""
    # This would get visualizations from database
    # For now, return empty list
    return []


@router.get("/visualizations/{viz_id}", response_model=DataVisualizationResponse)
async def get_visualization(
    viz_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Get a specific visualization."""
    # This would get visualization from database
    raise HTTPException(status_code=404, detail="Visualization not found")


@router.delete("/visualizations/{viz_id}")
async def delete_visualization(
    viz_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Delete a visualization."""
    # This would delete visualization from database
    return {"message": "Visualization deleted successfully"}


# Real-time Data (WebSocket)
@router.websocket("/sources/{source_id}/ws")
async def websocket_data_stream(
    websocket: WebSocket, source_id: str, user_id: Optional[str] = None
):
    """WebSocket endpoint for real-time data updates."""
    await data_stream_service.handle_websocket_connection(
        websocket, source_id, user_id or "anonymous"
    )


@router.websocket("/ws")
async def websocket_global_stream(websocket: WebSocket, user_id: Optional[str] = None):
    """WebSocket endpoint for global real-time updates."""
    await data_stream_service.handle_websocket_connection(
        websocket, "global", user_id or "anonymous"
    )


# Real-time Data (Server-Sent Events fallback)
@router.get("/sources/{source_id}/stream")
async def stream_data_updates(
    source_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Stream real-time data updates for a source using Server-Sent Events."""

    async def event_generator():
        yield "data: Connected to data stream\n\n"
        # This is a fallback for clients that don't support WebSockets
        # In practice, you'd implement actual SSE streaming here
        import asyncio
        from datetime import datetime

        try:
            while True:
                # Send periodic updates
                yield f'data: {{"type": "heartbeat", "timestamp": "{datetime.utcnow().isoformat()}"}}\n\n'
                await asyncio.sleep(30)
        except Exception:

            break


    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return connection_manager.get_connection_stats()


# Data Quality
@router.get("/sources/{source_id}/quality", response_model=DataQualityAnalysis)
async def analyze_data_quality(
    source_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Analyze data quality for a source."""
    return await service.analyze_data_quality(source_id)


# Data Lineage
@router.get("/sources/{source_id}/lineage", response_model=DataLineage)
async def get_data_lineage(
    source_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Get data lineage for a source."""
    # This would implement data lineage tracking
    # For now, return empty lineage
    return DataLineage(upstream=[], downstream=[])


# Collaboration
@router.post("/shared-views")
async def share_data_view(
    request: dict, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Share a data view with others."""
    # This would implement data view sharing
    # For now, return a mock response
    return {
        "share_id": "share_123",
        "share_url": "https://app.example.com/shared/share_123",
    }


@router.get("/shared-views/{share_id}")
async def get_shared_view(
    share_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
):
    """Get a shared data view."""
    # This would get shared view from database
    raise HTTPException(status_code=404, detail="Shared view not found")
