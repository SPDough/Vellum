import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import httpx
import pandas as pd
from playwright.async_api import async_playwright
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.data_source import (
    APISourceConfig,
    DataPullExecution,
    DataPullExecutionCreate,
    DataPullExecutionResponse,
    DataPullStatus,
    DataSourceConfiguration,
    DataSourceConfigurationCreate,
    DataSourceConfigurationResponse,
    DataSourceConfigurationUpdate,
    DataSourceTestRequest,
    DataSourceTestResponse,
    DataSourceType,
    MCPServerConfig,
    ProcessingConfig,
    ScheduleType,
    WebScrapingConfig,
)
from app.services.base import BaseService
from app.services.mcp_service import MCPService


logger = logging.getLogger(__name__)


class DataSourceService(BaseService):
    """Service for managing scheduled data pull workflows."""

    def __init__(self, db_session: AsyncSession, mcp_service: Optional[MCPService] = None):
        super().__init__(db_session)
        self.mcp_service = mcp_service

    async def create_configuration(
        self, config_data: DataSourceConfigurationCreate
    ) -> DataSourceConfigurationResponse:
        """Create a new data source configuration."""
        config_id = str(uuid.uuid4())

        # Validate source configuration
        await self._validate_source_config(config_data.data_source_type, config_data.source_config)

        config = DataSourceConfiguration(
            id=config_id,
            name=config_data.name,
            description=config_data.description,
            data_source_type=config_data.data_source_type.value,
            source_config=config_data.source_config,
            processing_config=config_data.processing_config or {},
            schedule_type=config_data.schedule_type.value,
            schedule_config=config_data.schedule_config or {},
            output_to_sandbox=config_data.output_to_sandbox,
            output_table_name=config_data.output_table_name or f"data_source_{config_id[:8]}",
            created_by=config_data.created_by,
        )

        # Calculate next run time if scheduled
        if config_data.schedule_type != ScheduleType.MANUAL:
            config.next_run_at = self._calculate_next_run(
                config_data.schedule_type, config_data.schedule_config or {}
            )

        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)

        return DataSourceConfigurationResponse.model_validate(config)

    async def get_configuration(self, config_id: str) -> Optional[DataSourceConfigurationResponse]:
        """Get a data source configuration by ID."""
        result = await self.db.execute(
            select(DataSourceConfiguration).where(DataSourceConfiguration.id == config_id)
        )
        config = result.scalar_one_or_none()

        if config:
            return DataSourceConfigurationResponse.model_validate(config)
        return None

    async def list_configurations(
        self,
        created_by: Optional[str] = None,
        data_source_type: Optional[DataSourceType] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DataSourceConfigurationResponse]:
        """List data source configurations with optional filters."""
        query = select(DataSourceConfiguration)

        if created_by:
            query = query.where(DataSourceConfiguration.created_by == created_by)
        if data_source_type:
            query = query.where(DataSourceConfiguration.data_source_type == data_source_type.value)
        if is_active is not None:
            query = query.where(DataSourceConfiguration.is_active == is_active)

        query = query.order_by(DataSourceConfiguration.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        configs = result.scalars().all()

        return [DataSourceConfigurationResponse.model_validate(config) for config in configs]

    async def update_configuration(
        self, config_id: str, update_data: DataSourceConfigurationUpdate
    ) -> Optional[DataSourceConfigurationResponse]:
        """Update a data source configuration."""
        result = await self.db.execute(
            select(DataSourceConfiguration).where(DataSourceConfiguration.id == config_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            return None

        # Update fields
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(config, field, value)

        config.updated_at = datetime.utcnow()

        # Recalculate next run time if schedule changed
        if update_data.schedule_type or update_data.schedule_config:
            if config.schedule_type != ScheduleType.MANUAL.value:
                config.next_run_at = self._calculate_next_run(
                    ScheduleType(config.schedule_type), config.schedule_config
                )

        await self.db.commit()
        await self.db.refresh(config)

        return DataSourceConfigurationResponse.model_validate(config)

    async def delete_configuration(self, config_id: str) -> bool:
        """Delete a data source configuration."""
        result = await self.db.execute(
            select(DataSourceConfiguration).where(DataSourceConfiguration.id == config_id)
        )
        config = result.scalar_one_or_none()

        if config:
            await self.db.delete(config)
            await self.db.commit()
            return True
        return False

    async def test_configuration(self, test_request: DataSourceTestRequest) -> DataSourceTestResponse:
        """Test a data source configuration without saving it."""
        try:
            start_time = datetime.utcnow()

            # Pull sample data
            data = await self._pull_data(
                test_request.data_source_type,
                test_request.source_config,
                sample_size=test_request.sample_size
            )

            # Apply processing if specified
            if test_request.processing_config and data:
                data = await self._process_data(data, test_request.processing_config)

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # Convert to list of dicts for JSON serialization
            if isinstance(data, pd.DataFrame):
                sample_data = data.head(test_request.sample_size).to_dict('records')
                record_count = len(data)
                data_schema = {col: str(dtype) for col, dtype in data.dtypes.items()}
            else:
                sample_data = data[:test_request.sample_size] if data else []
                record_count = len(data) if data else 0
                data_schema = {}

            return DataSourceTestResponse(
                success=True,
                sample_data=sample_data,
                record_count=record_count,
                execution_time_seconds=execution_time,
                data_schema=data_schema
            )

        except Exception as e:
            logger.error(f"Error testing data source: {str(e)}")
            return DataSourceTestResponse(
                success=False,
                error_message=str(e)
            )

    async def execute_data_pull(
        self, config_id: str, trigger_type: str = "MANUAL", triggered_by: str = "system"
    ) -> DataPullExecutionResponse:
        """Execute a data pull for a specific configuration."""
        config = await self.get_configuration(config_id)
        if not config:
            raise ValueError(f"Configuration {config_id} not found")

        execution_id = str(uuid.uuid4())
        execution = DataPullExecution(
            id=execution_id,
            configuration_id=config_id,
            status=DataPullStatus.PENDING.value,
            trigger_type=trigger_type,
            triggered_by=triggered_by
        )

        self.db.add(execution)
        await self.db.commit()

        try:
            # Update status to running
            execution.status = DataPullStatus.RUNNING.value
            execution.started_at = datetime.utcnow()
            await self.db.commit()

            # Pull data
            data = await self._pull_data(
                DataSourceType(config.data_source_type),
                config.source_config
            )

            # Process data if needed
            if config.processing_config:
                data = await self._process_data(data, config.processing_config)

            # Store data if output to sandbox is enabled
            output_location = None
            if config.output_to_sandbox and data is not None:
                output_location = await self._store_data_in_sandbox(
                    data, config.output_table_name
                )

            # Update execution with success
            execution.status = DataPullStatus.COMPLETED.value
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = int(
                (execution.completed_at - execution.started_at).total_seconds()
            )

            if isinstance(data, pd.DataFrame):
                execution.records_processed = len(data)
                execution.records_successful = len(data)
                execution.data_size_bytes = data.memory_usage(deep=True).sum()
            elif data:
                execution.records_processed = len(data)
                execution.records_successful = len(data)

            execution.output_location = output_location

            # Update configuration stats
            await self._update_configuration_stats(config_id, True, execution.duration_seconds)

        except Exception as e:
            logger.error(f"Error executing data pull {execution_id}: {str(e)}")
            execution.status = DataPullStatus.FAILED.value
            execution.completed_at = datetime.utcnow()
            execution.error_message = str(e)

            if execution.started_at:
                execution.duration_seconds = int(
                    (execution.completed_at - execution.started_at).total_seconds()
                )

            # Update configuration stats
            await self._update_configuration_stats(config_id, False, execution.duration_seconds)

        await self.db.commit()
        await self.db.refresh(execution)

        return DataPullExecutionResponse.model_validate(execution)

    async def get_execution_history(
        self, config_id: str, limit: int = 50, offset: int = 0
    ) -> List[DataPullExecutionResponse]:
        """Get execution history for a configuration."""
        result = await self.db.execute(
            select(DataPullExecution)
            .where(DataPullExecution.configuration_id == config_id)
            .order_by(DataPullExecution.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        executions = result.scalars().all()

        return [DataPullExecutionResponse.model_validate(execution) for execution in executions]

    async def _validate_source_config(self, source_type: DataSourceType, config: Dict[str, Any]):
        """Validate source configuration based on type."""
        try:
            if source_type == DataSourceType.API:
                APISourceConfig(**config)
            elif source_type == DataSourceType.MCP_SERVER:
                MCPServerConfig(**config)
            elif source_type == DataSourceType.WEB_SCRAPING:
                WebScrapingConfig(**config)
        except Exception as e:
            raise ValueError(f"Invalid {source_type.value} configuration: {str(e)}")

    async def _pull_data(
        self, source_type: DataSourceType, config: Dict[str, Any], sample_size: Optional[int] = None
    ) -> Union[pd.DataFrame, List[Dict[str, Any]], None]:
        """Pull data from the specified source."""
        if source_type == DataSourceType.API:
            return await self._pull_api_data(config, sample_size)
        elif source_type == DataSourceType.MCP_SERVER:
            return await self._pull_mcp_data(config, sample_size)
        elif source_type == DataSourceType.WEB_SCRAPING:
            return await self._pull_web_scraping_data(config, sample_size)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

    async def _pull_api_data(
        self, config: Dict[str, Any], sample_size: Optional[int] = None
    ) -> Union[pd.DataFrame, List[Dict[str, Any]]]:
        """Pull data from API endpoint."""
        api_config = APISourceConfig(**config)

        async with httpx.AsyncClient() as client:
            headers = api_config.headers or {}

            # Add authentication headers
            if api_config.auth_type and api_config.auth_config:
                if api_config.auth_type == "bearer":
                    headers["Authorization"] = f"Bearer {api_config.auth_config.get('token')}"
                elif api_config.auth_type == "api_key":
                    key_name = api_config.auth_config.get("key_name", "X-API-Key")
                    headers[key_name] = api_config.auth_config.get("key")

            response = await client.request(
                method=api_config.method,
                url=api_config.url,
                headers=headers,
                params=api_config.params,
                timeout=api_config.timeout_seconds
            )
            response.raise_for_status()

            if api_config.response_format == "json":
                data = response.json()
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict) and "data" in data:
                    df = pd.DataFrame(data["data"])
                else:
                    df = pd.DataFrame([data])

                if sample_size and len(df) > sample_size:
                    df = df.head(sample_size)

                return df
            elif api_config.response_format == "csv":
                from io import StringIO
                df = pd.read_csv(StringIO(response.text))

                if sample_size and len(df) > sample_size:
                    df = df.head(sample_size)

                return df
            else:
                return [{"response": response.text}]

    async def _pull_mcp_data(
        self, config: Dict[str, Any], sample_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Pull data from MCP server."""
        if not self.mcp_service:
            raise ValueError("MCP service not available")

        mcp_config = MCPServerConfig(**config)

        result = await self.mcp_service.call_tool(
            mcp_config.server_name,
            mcp_config.tool_name,
            mcp_config.tool_arguments or {}
        )

        if isinstance(result, list):
            data = result
        elif isinstance(result, dict):
            data = [result]
        else:
            data = [{"result": result}]

        if sample_size and len(data) > sample_size:
            data = data[:sample_size]

        return data

    async def _pull_web_scraping_data(
        self, config: Dict[str, Any], sample_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Pull data using web scraping."""
        scraping_config = WebScrapingConfig(**config)

        async with async_playwright() as p:
            browser = await p.chromium.launch()

            try:
                page = await browser.new_page()

                # Set headers if provided
                if scraping_config.headers:
                    await page.set_extra_http_headers(scraping_config.headers)

                # Set cookies if provided
                if scraping_config.cookies:
                    await page.context.add_cookies(scraping_config.cookies)

                # Navigate to page
                await page.goto(
                    scraping_config.url,
                    timeout=scraping_config.timeout_seconds * 1000
                )

                # Wait for content if specified
                if scraping_config.wait_config:
                    if "selector" in scraping_config.wait_config:
                        await page.wait_for_selector(scraping_config.wait_config["selector"])
                    elif "timeout" in scraping_config.wait_config:
                        await page.wait_for_timeout(scraping_config.wait_config["timeout"])

                # Extract data using selectors
                data = []
                for field_name, selector in scraping_config.selector_config.items():
                    elements = await page.query_selector_all(selector)
                    values = []
                    for element in elements:
                        text = await element.text_content()
                        values.append(text.strip() if text else "")

                    # Ensure all records have the same length
                    if not data:
                        data = [{field_name: value} for value in values]
                    else:
                        for i, value in enumerate(values):
                            if i < len(data):
                                data[i][field_name] = value

                if sample_size and len(data) > sample_size:
                    data = data[:sample_size]

                return data

            finally:
                await browser.close()

    async def _process_data(
        self, data: Union[pd.DataFrame, List[Dict[str, Any]]], config: Dict[str, Any]
    ) -> Union[pd.DataFrame, List[Dict[str, Any]]]:
        """Process data using pandas operations."""
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data.copy()

        processing_config = ProcessingConfig(**config)

        # Data cleaning
        if processing_config.data_cleaning:
            cleaning = processing_config.data_cleaning
            if cleaning.get("drop_duplicates"):
                df = df.drop_duplicates()
            if cleaning.get("fill_nulls"):
                df = df.fillna(cleaning["fill_nulls"])

        # Transformations
        if processing_config.transformations:
            for transform in processing_config.transformations:
                if transform["type"] == "rename_column":
                    df = df.rename(columns={transform["old_name"]: transform["new_name"]})
                elif transform["type"] == "convert_type":
                    df[transform["column"]] = df[transform["column"]].astype(transform["dtype"])
                elif transform["type"] == "add_column":
                    df[transform["name"]] = transform["value"]

        # Filters
        if processing_config.filters:
            for filter_config in processing_config.filters:
                column = filter_config["column"]
                operator = filter_config["operator"]
                value = filter_config["value"]

                if operator == "eq":
                    df = df[df[column] == value]
                elif operator == "ne":
                    df = df[df[column] != value]
                elif operator == "gt":
                    df = df[df[column] > value]
                elif operator == "lt":
                    df = df[df[column] < value]
                elif operator == "contains":
                    df = df[df[column].str.contains(str(value), na=False)]

        return df

    async def _store_data_in_sandbox(self, data: Union[pd.DataFrame, List[Dict[str, Any]]], table_name: str) -> str:
        """Store data in the data sandbox."""
        # This is a placeholder - implement based on your data sandbox storage mechanism
        # Could be database, file system, or other storage

        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data

        # For now, return a mock location
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        location = f"sandbox/{table_name}_{timestamp}.parquet"

        # In a real implementation, you would save the data:
        # df.to_parquet(location)

        return location

    async def _update_configuration_stats(self, config_id: str, success: bool, duration_seconds: Optional[int]):
        """Update configuration statistics after execution."""
        result = await self.db.execute(
            select(DataSourceConfiguration).where(DataSourceConfiguration.id == config_id)
        )
        config = result.scalar_one_or_none()

        if config:
            config.total_runs += 1
            config.last_run_at = datetime.utcnow()

            if success:
                config.successful_runs += 1
            else:
                config.failed_runs += 1

            if duration_seconds:
                if config.avg_execution_time_seconds:
                    config.avg_execution_time_seconds = int(
                        (config.avg_execution_time_seconds + duration_seconds) / 2
                    )
                else:
                    config.avg_execution_time_seconds = duration_seconds

            await self.db.commit()

    def _calculate_next_run(self, schedule_type: ScheduleType, config: Dict[str, Any]) -> datetime:
        """Calculate the next run time based on schedule configuration."""
        now = datetime.utcnow()

        if schedule_type == ScheduleType.INTERVAL:
            if "interval_seconds" in config:
                return now + timedelta(seconds=config["interval_seconds"])
            elif "interval_minutes" in config:
                return now + timedelta(minutes=config["interval_minutes"])
            elif "interval_hours" in config:
                return now + timedelta(hours=config["interval_hours"])
            elif "interval_days" in config:
                return now + timedelta(days=config["interval_days"])

        # For CRON scheduling, you would use a cron library like croniter
        # For now, default to 1 hour
        return now + timedelta(hours=1)