import io

from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional


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

from app.core.database import get_db, get_sync_db

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
from app.services.data_sandbox_service import DataSandboxService
from app.services.websocket_service import connection_manager, data_stream_service


router = APIRouter()


async def get_data_sandbox_service(
    db: Session = Depends(get_sync_db),
) -> DataSandboxService:
    """Get data sandbox service instance."""
    return DataSandboxService(db)


# Data Sources
@router.post("/sources", response_model=DataSourceResponse)
async def create_data_source(
    data_source: DataSourceCreate,
    service: DataSandboxService = Depends(get_data_sandbox_service),
) -> DataSourceResponse:
    """Create a new data source."""
    result = await service.create_data_source(data_source)
    return DataSourceResponse.from_orm(result)


@router.get("/sources", response_model=List[DataSourceResponse])
async def list_data_sources(
    service: DataSandboxService = Depends(get_data_sandbox_service),
) -> List[DataSourceResponse]:
    """List all data sources."""
    return await service.get_data_sources()


@router.get("/sources/{source_id}", response_model=DataSourceResponse)
async def get_data_source(
    source_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> DataSourceResponse:
    """Get a specific data source."""
    data_source = await service.get_data_source(source_id)
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return DataSourceResponse.from_orm(data_source)


@router.put("/sources/{source_id}", response_model=DataSourceResponse)
async def update_data_source(
    source_id: str,
    updates: DataSourceUpdate,
    service: DataSandboxService = Depends(get_data_sandbox_service),
) -> DataSourceResponse:
    """Update a data source."""
    data_source = await service.update_data_source(source_id, updates)
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return DataSourceResponse.from_orm(data_source)


@router.delete("/sources/{source_id}")
async def delete_data_source(
    source_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> Dict[str, str]:
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
) -> DataQueryResult:
    """Get a preview of data from a source."""
    data, total_count, execution_time = await service.get_data_preview(source_id, limit)
    data_source = await service.get_data_source(source_id)

    return DataQueryResult(
        data=data,
        total_count=total_count,
        schema=None,  # TODO: Fix schema type conversion
        execution_time=execution_time,
        source=DataSourceResponse.from_orm(data_source) if data_source else None,
    )


# Data Querying
@router.post("/query", response_model=DataQueryResult)
async def query_data(
    query: DataQuery, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> DataQueryResult:
    """Execute a data query."""
    data, total_count, execution_time = await service.query_data(query)
    data_source = await service.get_data_source(query.source)

    return DataQueryResult(
        data=data,
        total_count=total_count,
        schema=None,  # TODO: Fix schema type conversion
        execution_time=execution_time,
        source=DataSourceResponse.from_orm(data_source) if data_source else None,
    )


@router.post("/sql", response_model=DataQueryResult)
async def execute_sql(
    sql_request: dict, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> DataQueryResult:
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
) -> List[WorkflowOutput]:
    """Get workflow outputs."""
    # This would integrate with the workflow service
    # For now, return mock data
    return []


@router.get("/workflow-outputs/{output_id}", response_model=WorkflowOutput)
async def get_workflow_output(
    output_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> WorkflowOutput:
    """Get a specific workflow output."""
    # This would integrate with the workflow service
    raise HTTPException(status_code=404, detail="Workflow output not found")


@router.post("/sources/from-workflow", response_model=DataSourceResponse)
async def create_data_source_from_workflow(
    request: dict, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> DataSourceResponse:
    """Create a data source from workflow outputs."""
    workflow_id = request.get("workflow_id")
    output_name = request.get("output_name")

    if not workflow_id or not output_name:
        raise HTTPException(
            status_code=400, detail="workflow_id and output_name are required"
        )

    result = await service.create_data_source_from_workflow(workflow_id, output_name)
    return DataSourceResponse.from_orm(result)


# MCP Integration
@router.get("/mcp-streams", response_model=List[MCPDataStream])
async def get_mcp_data_streams(
    server_id: Optional[str] = None,
    stream_name: Optional[str] = None,
    limit: Optional[int] = None,
    since: Optional[str] = None,
    service: DataSandboxService = Depends(get_data_sandbox_service),
) -> List[MCPDataStream]:
    """Get MCP data streams."""
    # This would integrate with the MCP service
    # For now, return mock data
    return []


@router.get("/mcp-streams/{stream_id}", response_model=MCPDataStream)
async def get_mcp_data_stream(
    stream_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> MCPDataStream:
    """Get a specific MCP data stream."""
    # This would integrate with the MCP service
    raise HTTPException(status_code=404, detail="MCP data stream not found")


@router.post("/sources/from-mcp", response_model=DataSourceResponse)
async def create_data_source_from_mcp(
    request: dict, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> DataSourceResponse:
    """Create a data source from MCP stream."""
    server_id = request.get("server_id")
    stream_name = request.get("stream_name")

    if not server_id or not stream_name:
        raise HTTPException(
            status_code=400, detail="server_id and stream_name are required"
        )

    result = await service.create_data_source_from_mcp(server_id, stream_name)
    return DataSourceResponse.from_orm(result)


# Agent Integration
@router.get("/agent-results", response_model=List[AgentResult])
async def get_agent_results(
    agent_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: Optional[int] = None,
    since: Optional[str] = None,
    service: DataSandboxService = Depends(get_data_sandbox_service),
) -> List[AgentResult]:
    """Get agent results."""
    # This would integrate with the agent service
    # For now, return mock data
    return []


@router.get("/agent-results/{result_id}", response_model=AgentResult)
async def get_agent_result(
    result_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> AgentResult:
    """Get a specific agent result."""
    # This would integrate with the agent service
    raise HTTPException(status_code=404, detail="Agent result not found")


@router.post("/sources/from-agent", response_model=DataSourceResponse)
async def create_data_source_from_agent(
    request: dict, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> DataSourceResponse:
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

    result = await service.create_data_source(data_source_create)
    return DataSourceResponse.from_orm(result)


# Data Export
@router.post("/export")
async def export_data(
    request: DataExportRequest,
    service: DataSandboxService = Depends(get_data_sandbox_service),
) -> Dict[str, Any]:
    """Export data in the specified format."""
    data_str = await service.export_data(
        request.query, request.format, request.filename
    )

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

    return {
        "data": data_str,
        "filename": filename,
        "format": request.format,
        "exported_at": datetime.utcnow().isoformat(),
    }


@router.post("/scheduled-exports")
async def schedule_export(
    request: dict, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> Dict[str, str]:
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
) -> DataQueryResult:
    """Transform data from a source."""
    # This would implement data transformation
    # For now, return the original data
    data, total_count, execution_time = await service.get_data_preview(source_id, 100)
    data_source = await service.get_data_source(source_id)

    return DataQueryResult(
        data=data,
        total_count=total_count,
        schema=None,  # TODO: Fix schema type conversion
        execution_time=execution_time,
        source=DataSourceResponse.from_orm(data_source) if data_source else None,
    )


@router.post("/transformations", response_model=DataSourceResponse)
async def save_transformation(
    request: dict, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> DataSourceResponse:
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

    result = await service.create_data_source(data_source_create)
    return DataSourceResponse.from_orm(result)


# Visualizations
@router.post("/visualizations", response_model=DataVisualizationResponse)
async def save_visualization(
    config: DataVisualizationCreate,
    service: DataSandboxService = Depends(get_data_sandbox_service),
) -> DataVisualizationResponse:
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
) -> List[DataVisualizationResponse]:
    """Get all saved visualizations."""
    # This would get visualizations from database
    # For now, return empty list
    return []


@router.get("/visualizations/{viz_id}", response_model=DataVisualizationResponse)
async def get_visualization(
    viz_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> DataVisualizationResponse:
    """Get a specific visualization."""
    # This would get visualization from database
    raise HTTPException(status_code=404, detail="Visualization not found")


@router.delete("/visualizations/{viz_id}")
async def delete_visualization(
    viz_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> Dict[str, str]:
    """Delete a visualization."""
    # This would delete visualization from database
    return {"message": "Visualization deleted successfully"}


# Real-time Data (WebSocket)
@router.websocket("/sources/{source_id}/ws")
async def websocket_data_stream(
    websocket: WebSocket, source_id: str, user_id: Optional[str] = None
) -> None:
    """WebSocket endpoint for real-time data updates."""
    await data_stream_service.handle_websocket_connection(
        websocket, source_id, user_id or "anonymous"
    )


@router.websocket("/ws")
async def websocket_global_stream(
    websocket: WebSocket, user_id: Optional[str] = None
) -> None:
    """WebSocket endpoint for global real-time updates."""
    await data_stream_service.handle_websocket_connection(
        websocket, "global", user_id or "anonymous"
    )


# Real-time Data (Server-Sent Events fallback)
@router.get("/sources/{source_id}/stream")
async def stream_data_updates(
    source_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> StreamingResponse:
    """Stream real-time data updates for a source using Server-Sent Events."""

    async def event_generator() -> AsyncGenerator[str, None]:

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

            return

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/ws/stats")
async def get_websocket_stats() -> Dict[str, Any]:
    """Get WebSocket connection statistics."""
    return connection_manager.get_connection_stats()


# Data Quality
@router.get("/sources/{source_id}/quality", response_model=DataQualityAnalysis)
async def analyze_data_quality(
    source_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> DataQualityAnalysis:
    """Analyze data quality for a source."""
    return await service.analyze_data_quality(source_id)


# Data Lineage
@router.get("/sources/{source_id}/lineage", response_model=DataLineage)
async def get_data_lineage(
    source_id: str, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> DataLineage:
    """Get data lineage for a source."""
    # This would implement data lineage tracking
    # For now, return empty lineage
    return DataLineage(upstream=[], downstream=[])


# Collaboration
@router.post("/shared-views")
async def share_data_view(
    request: dict, service: DataSandboxService = Depends(get_data_sandbox_service)
) -> Dict[str, str]:
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
) -> Dict[str, Any]:
    """Get a shared data view."""
    # This would get shared view from database
    raise HTTPException(status_code=404, detail="Shared view not found")
