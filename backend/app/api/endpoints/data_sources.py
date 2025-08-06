from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.data_source import (
    DataPullExecutionResponse,
    DataSourceConfigurationCreate,
    DataSourceConfigurationResponse,
    DataSourceConfigurationUpdate,
    DataSourceTestRequest,
    DataSourceTestResponse,
    DataSourceType,
)
from app.services.data_source_service import DataSourceService
from app.services.mcp_service import MCPService

router = APIRouter(prefix="/data-sources", tags=["data-sources"])


def get_data_source_service(db: AsyncSession = Depends(get_db)) -> DataSourceService:
    """Get data source service instance."""
    # You may want to inject MCP service here if available
    return DataSourceService(db)


@router.post("/", response_model=DataSourceConfigurationResponse)
async def create_data_source(
    config_data: DataSourceConfigurationCreate,
    service: DataSourceService = Depends(get_data_source_service)
) -> DataSourceConfigurationResponse:
    """Create a new data source configuration."""
    try:
        return await service.create_configuration(config_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create data source: {str(e)}")


@router.get("/", response_model=List[DataSourceConfigurationResponse])
async def list_data_sources(
    created_by: Optional[str] = Query(None, description="Filter by creator"),
    data_source_type: Optional[DataSourceType] = Query(None, description="Filter by type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    service: DataSourceService = Depends(get_data_source_service)
) -> List[DataSourceConfigurationResponse]:
    """List data source configurations with optional filters."""
    try:
        return await service.list_configurations(
            created_by=created_by,
            data_source_type=data_source_type,
            is_active=is_active,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list data sources: {str(e)}")


@router.get("/{config_id}", response_model=DataSourceConfigurationResponse)
async def get_data_source(
    config_id: str,
    service: DataSourceService = Depends(get_data_source_service)
) -> DataSourceConfigurationResponse:
    """Get a specific data source configuration."""
    config = await service.get_configuration(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Data source configuration not found")
    return config


@router.put("/{config_id}", response_model=DataSourceConfigurationResponse)
async def update_data_source(
    config_id: str,
    update_data: DataSourceConfigurationUpdate,
    service: DataSourceService = Depends(get_data_source_service)
) -> DataSourceConfigurationResponse:
    """Update a data source configuration."""
    try:
        config = await service.update_configuration(config_id, update_data)
        if not config:
            raise HTTPException(status_code=404, detail="Data source configuration not found")
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update data source: {str(e)}")


@router.delete("/{config_id}")
async def delete_data_source(
    config_id: str,
    service: DataSourceService = Depends(get_data_source_service)
) -> dict:
    """Delete a data source configuration."""
    try:
        success = await service.delete_configuration(config_id)
        if not success:
            raise HTTPException(status_code=404, detail="Data source configuration not found")
        return {"message": "Data source configuration deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete data source: {str(e)}")


@router.post("/test", response_model=DataSourceTestResponse)
async def test_data_source(
    test_request: DataSourceTestRequest,
    service: DataSourceService = Depends(get_data_source_service)
) -> DataSourceTestResponse:
    """Test a data source configuration without saving it."""
    try:
        return await service.test_configuration(test_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test data source: {str(e)}")


@router.post("/{config_id}/execute", response_model=DataPullExecutionResponse)
async def execute_data_pull(
    config_id: str,
    trigger_type: str = "MANUAL",
    triggered_by: str = "user",
    service: DataSourceService = Depends(get_data_source_service)
) -> DataPullExecutionResponse:
    """Execute a data pull for a specific configuration."""
    try:
        return await service.execute_data_pull(
            config_id=config_id,
            trigger_type=trigger_type,
            triggered_by=triggered_by
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute data pull: {str(e)}")


@router.get("/{config_id}/executions", response_model=List[DataPullExecutionResponse])
async def get_execution_history(
    config_id: str,
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    service: DataSourceService = Depends(get_data_source_service)
) -> List[DataPullExecutionResponse]:
    """Get execution history for a data source configuration."""
    try:
        return await service.get_execution_history(
            config_id=config_id,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get execution history: {str(e)}")


@router.get("/{config_id}/status")
async def get_data_source_status(
    config_id: str,
    service: DataSourceService = Depends(get_data_source_service)
) -> dict:
    """Get the current status and metrics for a data source configuration."""
    try:
        config = await service.get_configuration(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Data source configuration not found")

        # Get recent execution history
        recent_executions = await service.get_execution_history(config_id, limit=5)

        # Calculate success rate
        success_rate = 0.0
        if config.total_runs > 0:

            success_rate = (config.successful_runs / config.total_runs) * 100

        return {
            "config_id": config_id,
            "name": config.name,
            "is_active": config.is_active,
            "last_run_at": config.last_run_at,
            "next_run_at": config.next_run_at,
            "total_runs": config.total_runs,
            "successful_runs": config.successful_runs,
            "failed_runs": config.failed_runs,
            "success_rate": round(success_rate, 2),
            "avg_execution_time_seconds": config.avg_execution_time_seconds,
            "recent_executions": recent_executions
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get data source status: {str(e)}")


@router.post("/{config_id}/toggle")
async def toggle_data_source(
    config_id: str,
    service: DataSourceService = Depends(get_data_source_service)
) -> dict:
    """Toggle the active status of a data source configuration."""
    try:
        config = await service.get_configuration(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Data source configuration not found")

        update_data = DataSourceConfigurationUpdate(is_active=not config.is_active)
        updated_config = await service.update_configuration(config_id, update_data)

        return {
            "config_id": config_id,
            "name": config.name,
            "is_active": updated_config.is_active,
            "message": f"Data source {'activated' if updated_config.is_active else 'deactivated'} successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle data source: {str(e)}")
