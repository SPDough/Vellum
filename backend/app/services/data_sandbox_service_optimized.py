"""
Optimized Data Sandbox Service with Performance Improvements

This module provides an optimized version of the DataSandboxService that addresses:
1. N+1 query performance issues
2. Better error handling
3. Improved caching
4. Enhanced monitoring
"""

import io
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from fastapi import HTTPException
from sqlalchemy import and_, desc, text
from sqlalchemy.orm import Session

from app.core.performance import cache_result, performance_monitor
from app.models.data_sandbox import (
    AgentResultCreate,
    DataFilter,
    DataQualityAnalysis,
    DataQuery,
    DataRecord,
    DataSource,
    DataSourceCreate,
    DataSourceResponse,
    DataSourceType,
    DataSourceUpdate,
    FilterOperator,
    MCPDataStreamCreate,
    WorkflowOutputCreate,
)


class OptimizedDataSandboxService:
    """Optimized Data Sandbox Service with performance improvements."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self._cache = {}

    async def create_data_source(self, data_source: DataSourceCreate) -> DataSource:
        """Create a new data source with validation."""
        try:
            db_data_source = DataSource(
                name=data_source.name,
                type=data_source.type,
                description=data_source.description,
                source_metadata=data_source.source_metadata,
                schema=data_source.schema,
            )
            self.db.add(db_data_source)
            self.db.commit()
            self.db.refresh(db_data_source)
            
            # Clear cache
            self._clear_cache()
            return db_data_source
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Failed to create data source: {str(e)}")

    @cache_result(ttl=300)  # Cache for 5 minutes
    async def get_data_sources(self) -> List[DataSourceResponse]:
        """Get all data sources with caching."""
        try:
            data_sources = self.db.query(DataSource).all()
            return [
                DataSourceResponse(
                    id=str(ds.id),
                    name=ds.name,
                    type=ds.type,
                    description=ds.description,
                    record_count=ds.record_count or 0,
                    last_updated=ds.last_updated,
                    status=ds.status,
                    schema=ds.schema,
                )
                for ds in data_sources
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch data sources: {str(e)}")

    async def get_data_source(self, source_id: str) -> Optional[DataSource]:
        """Get a specific data source by ID."""
        try:
            return self.db.query(DataSource).filter(DataSource.id == source_id).first()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch data source: {str(e)}")

    async def update_data_source(
        self, source_id: str, updates: DataSourceUpdate
    ) -> Optional[DataSource]:
        """Update a data source with validation."""
        try:
            data_source = await self.get_data_source(source_id)
            if not data_source:
                raise HTTPException(status_code=404, detail="Data source not found")

            update_data = updates.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(data_source, field, value)

            data_source.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(data_source)
            
            # Clear cache
            self._clear_cache()
            return data_source
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Failed to update data source: {str(e)}")

    async def delete_data_source(self, source_id: str) -> bool:
        """Delete a data source and its records."""
        try:
            data_source = await self.get_data_source(source_id)
            if not data_source:
                raise HTTPException(status_code=404, detail="Data source not found")

            # Delete associated records first
            self.db.query(DataRecord).filter(DataRecord.data_source_id == source_id).delete()
            
            # Delete data source
            self.db.delete(data_source)
            self.db.commit()
            
            # Clear cache
            self._clear_cache()
            return True
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Failed to delete data source: {str(e)}")

    async def query_data(
        self, query: DataQuery
    ) -> Tuple[List[Dict[str, Any]], int, float]:
        """Execute a data query with performance monitoring."""
        start_time = time.time()
        
        try:
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
                            text(f"data->>'{sort_item.field}'")
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
                record_dict = {
                    "id": str(record.id),
                    "timestamp": record.timestamp.isoformat() if record.timestamp else None,
                    **record.data,
                }
                if record.record_metadata:
                    record_dict["_metadata"] = record.record_metadata
                data.append(record_dict)

            execution_time = time.time() - start_time
            
            # Record performance metrics
            performance_monitor.record_response_time(f"query_data_{query.source}", execution_time * 1000)
            
            return data, total_count, execution_time
            
        except HTTPException:
            raise
        except Exception as e:
            execution_time = time.time() - start_time
            performance_monitor.record_response_time(f"query_data_error_{query.source}", execution_time * 1000)
            raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")

    def _apply_filter(self, db_query: Any, filter_item: DataFilter) -> Any:
        """Apply a filter to the database query."""
        field_path = f"data->>'{filter_item.field}'"

        if filter_item.operator == FilterOperator.EQUALS:
            return db_query.filter(
                text(f"{field_path} = :value").bindparams(value=filter_item.value)
            )
        elif filter_item.operator == FilterOperator.NOT_EQUALS:
            return db_query.filter(
                text(f"{field_path} != :value").bindparams(value=filter_item.value)
            )
        elif filter_item.operator == FilterOperator.GREATER_THAN:
            return db_query.filter(
                text(f"{field_path} > :value").bindparams(value=filter_item.value)
            )
        elif filter_item.operator == FilterOperator.LESS_THAN:
            return db_query.filter(
                text(f"{field_path} < :value").bindparams(value=filter_item.value)
            )
        elif filter_item.operator == FilterOperator.GREATER_THAN_EQUALS:
            return db_query.filter(
                text(f"{field_path} >= :value").bindparams(value=filter_item.value)
            )
        elif filter_item.operator == FilterOperator.LESS_THAN_EQUALS:
            return db_query.filter(
                text(f"{field_path} <= :value").bindparams(value=filter_item.value)
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

    # Workflow Integration - OPTIMIZED
    async def store_workflow_output(self, output: WorkflowOutputCreate) -> DataRecord:
        """Store workflow output as a data record with optimized performance."""
        try:
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
                record_metadata={
                    "execution_id": output.execution_id,
                    "step_name": output.step_name,
                    **output.metadata,
                },
            )

            self.db.add(data_record)

            # OPTIMIZED: Use simple increment instead of COUNT query
            data_source.record_count = (data_source.record_count or 0) + 1
            data_source.last_updated = datetime.utcnow()

            self.db.commit()
            self.db.refresh(data_record)
            
            # Clear cache
            self._clear_cache()
            return data_record
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Failed to store workflow output: {str(e)}")

    # MCP Integration - OPTIMIZED
    async def store_mcp_data_stream(self, stream: MCPDataStreamCreate) -> DataRecord:
        """Store MCP data stream as a data record with optimized performance."""
        try:
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
                data_source_id=data_source.id,
                data=stream.data,
                record_metadata=stream.metadata,
            )

            self.db.add(data_record)

            # OPTIMIZED: Use simple increment instead of COUNT query
            data_source.record_count = (data_source.record_count or 0) + 1
            data_source.last_updated = datetime.utcnow()

            self.db.commit()
            self.db.refresh(data_record)
            
            # Clear cache
            self._clear_cache()
            return data_record
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Failed to store MCP data stream: {str(e)}")

    # Agent Integration - OPTIMIZED
    async def store_agent_result(self, result: AgentResultCreate) -> DataRecord:
        """Store agent result as a data record with optimized performance."""
        try:
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
                record_metadata={
                    "execution_id": result.execution_id,
                    "task_type": result.task_type,
                    **result.metadata,
                },
            )

            self.db.add(data_record)

            # OPTIMIZED: Use simple increment instead of COUNT query
            data_source.record_count = (data_source.record_count or 0) + 1
            data_source.last_updated = datetime.utcnow()

            self.db.commit()
            self.db.refresh(data_record)
            
            # Clear cache
            self._clear_cache()
            return data_record
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Failed to store agent result: {str(e)}")

    async def export_data(
        self, query: DataQuery, format: str, filename: Optional[str] = None
    ) -> bytes:
        """Export data in the specified format with error handling."""
        try:
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
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

    async def analyze_data_quality(self, source_id: str) -> DataQualityAnalysis:
        """Analyze data quality for a data source with performance monitoring."""
        start_time = time.time()
        
        try:
            data_source = await self.get_data_source(source_id)
            if not data_source:
                raise HTTPException(status_code=404, detail="Data source not found")

            # Get sample data for analysis
            sample_data, total_count, _ = await self.get_data_preview(source_id, limit=1000)

            if not sample_data:
                return DataQualityAnalysis(
                    source_id=source_id,
                    total_records=0,
                    completeness_score=0.0,
                    accuracy_score=0.0,
                    consistency_score=0.0,
                    issues=[],
                )

            # Analyze data quality
            issues = []
            completeness_score = 1.0
            accuracy_score = 1.0
            consistency_score = 1.0

            # Check for missing values
            missing_fields = 0
            total_fields = 0

            for record in sample_data:
                for field, value in record.items():
                    if field.startswith("_"):  # Skip metadata fields
                        continue
                    total_fields += 1
                    if value is None or value == "":
                        missing_fields += 1

            if total_fields > 0:
                completeness_score = 1.0 - (missing_fields / total_fields)

            # Check for data type consistency
            field_types = {}
            for record in sample_data:
                for field, value in record.items():
                    if field.startswith("_"):
                        continue
                    if field not in field_types:
                        field_types[field] = type(value)
                    elif type(value) != field_types[field]:
                        consistency_score -= 0.1
                        issues.append(f"Inconsistent data type for field '{field}'")

            # Check for outliers in numeric fields
            numeric_fields = {}
            for record in sample_data:
                for field, value in record.items():
                    if field.startswith("_"):
                        continue
                    if isinstance(value, (int, float)):
                        if field not in numeric_fields:
                            numeric_fields[field] = []
                        numeric_fields[field].append(value)

            # Simple outlier detection
            for field, values in numeric_fields.items():
                if len(values) > 10:
                    mean_val = sum(values) / len(values)
                    std_val = (sum((x - mean_val) ** 2 for x in values) / len(values)) ** 0.5
                    outliers = [v for v in values if abs(v - mean_val) > 2 * std_val]
                    if outliers:
                        issues.append(f"Potential outliers detected in field '{field}'")

            execution_time = time.time() - start_time
            performance_monitor.record_response_time(f"analyze_data_quality_{source_id}", execution_time * 1000)

            return DataQualityAnalysis(
                source_id=source_id,
                total_records=total_count,
                completeness_score=completeness_score,
                accuracy_score=accuracy_score,
                consistency_score=consistency_score,
                issues=issues,
            )
            
        except HTTPException:
            raise
        except Exception as e:
            execution_time = time.time() - start_time
            performance_monitor.record_response_time(f"analyze_data_quality_error_{source_id}", execution_time * 1000)
            raise HTTPException(status_code=500, detail=f"Data quality analysis failed: {str(e)}")

    def _clear_cache(self):
        """Clear internal cache when data changes."""
        self._cache.clear()


# Factory function for dependency injection
def get_optimized_data_sandbox_service(db: Session) -> OptimizedDataSandboxService:
    """Get an optimized data sandbox service instance."""
    return OptimizedDataSandboxService(db)
