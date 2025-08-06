import io
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from fastapi import HTTPException
from sqlalchemy import and_, asc, desc, func, or_, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.data_sandbox import (
    AgentResultCreate,
    DataFilter,
    DataQualityAnalysis,
    DataQuery,
    DataRecord,
    DataSort,
    DataSource,
    DataSourceCreate,
    DataSourceResponse,
    DataSourceStatus,
    DataSourceType,
    DataSourceUpdate,
    DataTransformation,
    DataVisualization,
    FilterOperator,
    MCPDataStreamCreate,
    SharedDataView,
    WorkflowOutputCreate,
)


class DataSandboxService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # Data Source Management
    async def create_data_source(self, data_source: DataSourceCreate) -> DataSource:
        """Create a new data source."""
        db_data_source = DataSource(
            name=data_source.name,
            type=data_source.type.value,
            description=data_source.description,
            schema=data_source.data_schema.dict() if data_source.data_schema else None,
            source_metadata=data_source.source_metadata or {},
            config=data_source.config or {},
        )

        self.db.add(db_data_source)
        self.db.commit()
        self.db.refresh(db_data_source)
        return db_data_source

    async def get_data_sources(self) -> List[DataSourceResponse]:
        """Get all data sources."""
        sources = (
            self.db.query(DataSource).order_by(desc(DataSource.last_updated)).all()
        )
        return [DataSourceResponse.from_orm(source) for source in sources]

    async def get_data_source(self, source_id: str) -> Optional[DataSource]:
        """Get a specific data source."""
        source = self.db.query(DataSource).filter(DataSource.id == source_id).first()
        return source if source else None

    async def update_data_source(
        self, source_id: str, updates: DataSourceUpdate
    ) -> Optional[DataSource]:
        """Update a data source."""
        db_data_source = await self.get_data_source(source_id)
        if not db_data_source:
            return None

        update_data = updates.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "data_schema" and value:
                setattr(db_data_source, "schema", value.dict())
            elif field == "data_schema":
                setattr(db_data_source, "schema", value)
            else:
                setattr(db_data_source, field, value)

        db_data_source.last_updated = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_data_source)
        return db_data_source

    async def delete_data_source(self, source_id: str) -> bool:
        """Delete a data source and all its records."""
        db_data_source = await self.get_data_source(source_id)
        if not db_data_source:
            return False

        self.db.delete(db_data_source)
        self.db.commit()
        return True

    # Data Querying
    async def query_data(
        self, query: DataQuery
    ) -> Tuple[List[Dict[str, Any]], int, float]:
        """Execute a data query and return results."""
        start_time = time.time()

        # Get the data source
        data_source = await self.get_data_source(query.source)
        if not data_source:
            raise HTTPException(status_code=404, detail="Data source not found")

        # Build the base query
        db_query = self.db.query(DataRecord).filter(
            DataRecord.data_source_id == query.source
        )

        # Apply filters
        if query.filters:
            for filter_item in query.filters:
                db_query = self._apply_filter(db_query, filter_item)

        # Apply sorting
        if query.sorts:
            for sort_item in query.sorts:
                if sort_item.direction == "desc":
                    db_query = db_query.order_by(
                        desc(text(f"data->>'{sort_item.field}'"))
                    )
                else:
                    db_query = db_query.order_by(
                        asc(text(f"data->>'{sort_item.field}'"))
                    )

        # Get total count before applying limit/offset
        total_count = db_query.count()

        # Apply pagination
        if query.offset:
            db_query = db_query.offset(query.offset)
        if query.limit:
            db_query = db_query.limit(query.limit)

        # Execute query
        records = db_query.all()

        # Transform records to dict format
        data: List[Dict[str, Any]] = []
        for record in records:
            record_data: Dict[str, Any] = record.data.copy() if record.data else {}
            record_data["_id"] = record.id
            record_data["_timestamp"] = record.timestamp.isoformat()

            # Apply field selection if specified
            if query.fields:
                filtered_data: Dict[str, Any] = {
                    k: v
                    for k, v in record_data.items()
                    if k in query.fields or k.startswith("_")
                }
                record_data = filtered_data

            data.append(record_data)

        execution_time = time.time() - start_time
        return data, total_count, execution_time

    def _apply_filter(self, db_query: Any, filter_item: DataFilter) -> Any:
        """Apply a filter to the database query."""
        field_path = f"data->>'{filter_item.field}'"

        if filter_item.operator == FilterOperator.EQ:
            return db_query.filter(
                text(f"{field_path} = :value").bindparams(value=str(filter_item.value))
            )
        elif filter_item.operator == FilterOperator.NE:
            return db_query.filter(
                text(f"{field_path} != :value").bindparams(value=str(filter_item.value))
            )
        elif filter_item.operator == FilterOperator.GT:
            return db_query.filter(
                text(f"CAST({field_path} AS NUMERIC) > :value").bindparams(
                    value=filter_item.value
                )
            )
        elif filter_item.operator == FilterOperator.GTE:
            return db_query.filter(
                text(f"CAST({field_path} AS NUMERIC) >= :value").bindparams(
                    value=filter_item.value
                )
            )
        elif filter_item.operator == FilterOperator.LT:
            return db_query.filter(
                text(f"CAST({field_path} AS NUMERIC) < :value").bindparams(
                    value=filter_item.value
                )
            )
        elif filter_item.operator == FilterOperator.LTE:
            return db_query.filter(
                text(f"CAST({field_path} AS NUMERIC) <= :value").bindparams(
                    value=filter_item.value
                )
            )
        elif filter_item.operator == FilterOperator.IN:
            if isinstance(filter_item.value, list):
                placeholders = ",".join([f"'{v}'" for v in filter_item.value])
                return db_query.filter(text(f"{field_path} IN ({placeholders})"))
        elif filter_item.operator == FilterOperator.LIKE:
            return db_query.filter(
                text(f"{field_path} ILIKE :value").bindparams(
                    value=f"%{filter_item.value}%"
                )
            )
        elif filter_item.operator == FilterOperator.REGEX:
            return db_query.filter(
                text(f"{field_path} ~ :value").bindparams(value=filter_item.value)
            )

        return db_query

    async def get_data_preview(
        self, source_id: str, limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int, float]:
        """Get a preview of data from a source."""
        query = DataQuery(source=source_id, limit=limit)
        return await self.query_data(query)

    # Workflow Integration
    async def store_workflow_output(self, output: WorkflowOutputCreate) -> DataRecord:
        """Store workflow output as a data record."""
        # Find or create data source for this workflow
        source_name = f"Workflow: {output.workflow_name}"
        data_source = (
            self.db.query(DataSource)
            .filter(
                and_(
                    DataSource.type == DataSourceType.WORKFLOW,
                    DataSource.source_metadata["workflow_id"].astext
                    == output.workflow_id,
                )
            )
            .first()
        )

        if not data_source:
            # Create new data source for this workflow
            data_source = DataSource(
                name=source_name,
                type=DataSourceType.WORKFLOW,
                description=f"Data from workflow: {output.workflow_name}",
                source_metadata={
                    "workflow_id": output.workflow_id,
                    "workflow_name": output.workflow_name,
                },
                schema=output.data_schema.dict() if output.data_schema else None,
            )
            self.db.add(data_source)
            self.db.flush()

        # Create data record
        data_record = DataRecord(
            data_source_id=data_source.id,
            data=output.data,
            metadata={
                "execution_id": output.execution_id,
                "step_name": output.step_name,
                **output.metadata,
            },
        )

        self.db.add(data_record)

        # Update data source record count
        data_source.record_count = (
            self.db.query(DataRecord)
            .filter(DataRecord.data_source_id == data_source.id)
            .count()
            + 1
        )

        # Update data source record count efficiently
        data_source.record_count = (data_source.record_count or 0) + 1

        data_source.last_updated = datetime.utcnow()

        self.db.commit()
        self.db.refresh(data_record)
        return data_record

    async def create_data_source_from_workflow(
        self, workflow_id: str, output_name: str
    ) -> DataSource:
        """Create a data source from workflow outputs."""
        # This would integrate with the workflow service to get recent outputs
        # For now, create a placeholder data source
        data_source = DataSource(
            name=f"Workflow Output: {output_name}",
            type=DataSourceType.WORKFLOW,
            description=f"Data source created from workflow {workflow_id} output '{output_name}'",
            source_metadata={"workflow_id": workflow_id, "output_name": output_name},
        )

        self.db.add(data_source)
        self.db.commit()
        self.db.refresh(data_source)
        return data_source

    # MCP Integration
    async def store_mcp_data_stream(self, stream: MCPDataStreamCreate) -> DataRecord:
        """Store MCP data stream as a data record."""
        # Find or create data source for this MCP stream
        source_name = f"MCP: {stream.server_name} - {stream.stream_name}"
        data_source = (
            self.db.query(DataSource)
            .filter(
                and_(
                    DataSource.type == DataSourceType.MCP,
                    DataSource.source_metadata["server_id"].astext == stream.server_id,
                    DataSource.source_metadata["stream_name"].astext
                    == stream.stream_name,
                )
            )
            .first()
        )

        if not data_source:
            data_source = DataSource(
                name=source_name,
                type=DataSourceType.MCP,
                description=f"Data from MCP server: {stream.server_name}, stream: {stream.stream_name}",
                source_metadata={
                    "server_id": stream.server_id,
                    "server_name": stream.server_name,
                    "stream_name": stream.stream_name,
                },
                schema=stream.data_schema.dict() if stream.data_schema else None,
            )
            self.db.add(data_source)
            self.db.flush()

        # Create data record
        data_record = DataRecord(
            data_source_id=data_source.id, data=stream.data, metadata=stream.metadata
        )

        self.db.add(data_record)

        # Update data source record count
        data_source.record_count = (
            self.db.query(DataRecord)
            .filter(DataRecord.data_source_id == data_source.id)
            .count()
            + 1
        )

        # Update data source record count efficiently
        data_source.record_count = (data_source.record_count or 0) + 1

        data_source.last_updated = datetime.utcnow()

        self.db.commit()
        self.db.refresh(data_record)
        return data_record

    async def create_data_source_from_mcp(
        self, server_id: str, stream_name: str
    ) -> DataSource:
        """Create a data source from MCP stream."""
        data_source = DataSource(
            name=f"MCP Stream: {stream_name}",
            type=DataSourceType.MCP,
            description=f"Data source created from MCP server {server_id} stream '{stream_name}'",
            source_metadata={"server_id": server_id, "stream_name": stream_name},
        )

        self.db.add(data_source)
        self.db.commit()
        self.db.refresh(data_source)
        return data_source

    # Agent Integration
    async def store_agent_result(self, result: AgentResultCreate) -> DataRecord:
        """Store agent result as a data record."""
        # Find or create data source for this agent
        source_name = f"Agent: {result.agent_name}"
        data_source = (
            self.db.query(DataSource)
            .filter(
                and_(
                    DataSource.type == DataSourceType.AGENT,
                    DataSource.source_metadata["agent_id"].astext == result.agent_id,
                )
            )
            .first()
        )

        if not data_source:
            data_source = DataSource(
                name=source_name,
                type=DataSourceType.AGENT,
                description=f"Data from agent: {result.agent_name}",
                source_metadata={
                    "agent_id": result.agent_id,
                    "agent_name": result.agent_name,
                },
                schema=result.data_schema.dict() if result.data_schema else None,
            )
            self.db.add(data_source)
            self.db.flush()

        # Create data record
        data_record = DataRecord(
            data_source_id=data_source.id,
            data=result.result,
            metadata={
                "execution_id": result.execution_id,
                "task_type": result.task_type,
                **result.metadata,
            },
        )

        self.db.add(data_record)

        # Update data source record count
        data_source.record_count = (
            self.db.query(DataRecord)
            .filter(DataRecord.data_source_id == data_source.id)
            .count()
            + 1
        )

        # Update data source record count efficiently
        data_source.record_count = (data_source.record_count or 0) + 1

        data_source.last_updated = datetime.utcnow()

        self.db.commit()
        self.db.refresh(data_record)
        return data_record

    # Data Export
    async def export_data(
        self, query: DataQuery, format: str, filename: Optional[str] = None
    ) -> bytes:
        """Export data in the specified format."""
        data, total_count, execution_time = await self.query_data(query)

        if format == "json":
            return json.dumps(data, indent=2, default=str).encode("utf-8")

        elif format == "csv":
            if not data:
                return b""

            df = pd.DataFrame(data)
            output = io.StringIO()
            df.to_csv(output, index=False)
            return output.getvalue().encode("utf-8")

        elif format == "xlsx":
            if not data:
                return b""

            df = pd.DataFrame(data)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Data")
            return buffer.getvalue()

        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported export format: {format}"
            )

    # Data Quality Analysis
    async def analyze_data_quality(self, source_id: str) -> DataQualityAnalysis:
        """Analyze data quality for a data source."""
        data_source = await self.get_data_source(source_id)
        if not data_source:
            raise HTTPException(status_code=404, detail="Data source not found")

        # Get all records for this source
        records = (
            self.db.query(DataRecord)
            .filter(DataRecord.data_source_id == source_id)
            .all()
        )

        if not records:

            return DataQualityAnalysis(
                completeness=0.0,
                accuracy=0.0,
                consistency=0.0,
                timeliness=0.0,
                issues=[],
            )

        # Convert to DataFrame for analysis
        data_list = [record.data for record in records]
        df = pd.DataFrame(data_list)

        # Calculate quality metrics
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        completeness = (
            ((total_cells - missing_cells) / total_cells) * 100
            if total_cells > 0
            else 0
        )

        # Find issues
        issues = []

        # Missing values
        missing_by_column = df.isnull().sum()
        for column, missing_count in missing_by_column.items():
            if missing_count > 0:
                issues.append(
                    {
                        "type": "missing_values",
                        "count": int(missing_count),
                        "description": f"Column '{column}' has {missing_count} missing values",
                        "affected_fields": [column],
                    }
                )

        # Duplicates
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            issues.append(
                {
                    "type": "duplicates",
                    "count": int(duplicate_count),
                    "description": f"Found {duplicate_count} duplicate records",
                    "affected_fields": list(df.columns),
                }
            )

        return DataQualityAnalysis(
            completeness=completeness,
            accuracy=95.0,  # Placeholder - would need domain-specific rules
            consistency=90.0,  # Placeholder - would need consistency checks
            timeliness=85.0,  # Placeholder - would check data freshness
            issues=issues,
        )


# Singleton service instance


def get_data_sandbox_service(db: Optional[Session] = None) -> DataSandboxService:
    """Get singleton instance of DataSandboxService."""
    if db is None:
        from app.core.database import SessionLocal

        db = SessionLocal()
    return DataSandboxService(db)
