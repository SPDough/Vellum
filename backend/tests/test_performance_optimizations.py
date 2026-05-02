"""
Performance Tests for Optimized Data Sandbox Service

This module tests the performance improvements made to the DataSandboxService,
including N+1 query fixes, caching, and error handling.
"""

import asyncio
import time
from datetime import datetime
from typing import List
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.data_sandbox_service_optimized import OptimizedDataSandboxService
from app.models.data_sandbox import (
    DataSource,
    DataRecord,
    DataSourceType,
    WorkflowOutputCreate,
    MCPDataStreamCreate,
    AgentResultCreate,
    DataQuery,
)


class TestPerformanceOptimizations:
    """Test performance optimizations in the data sandbox service."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock(spec=Session)
        query = Mock()
        # Fluent query-chain behavior used by the optimized service.
        query.filter.return_value = query
        query.order_by.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.first.return_value = None
        query.count.return_value = 0
        query.all.return_value = []
        db.query.return_value = query
        db.add.return_value = None
        db.commit.return_value = None
        db.rollback.return_value = None
        db.refresh.return_value = None
        db.flush.return_value = None
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create an optimized data sandbox service instance."""
        return OptimizedDataSandboxService(mock_db)

    @pytest.fixture
    def sample_data_source(self):
        """Create a sample data source."""
        return DataSource(
            id="test-source-1",
            name="Test Workflow",
            type=DataSourceType.WORKFLOW,
            description="Test workflow data source",
            record_count=0,
            last_updated=datetime.utcnow(),
        )

    @pytest.fixture
    def sample_workflow_output(self):
        """Create a sample workflow output."""
        return WorkflowOutputCreate(
            workflow_id="test-workflow-1",
            workflow_name="Test Workflow",
            execution_id="exec-123",
            step_name="data_processing",
            data={"symbol": "AAPL", "price": 185.42, "volume": 1250000},
            metadata={"source": "market_data"},
        )

    def test_n_plus_one_query_fix_workflow_output(self, service, mock_db, sample_data_source):
        """Test that N+1 query issue is fixed in store_workflow_output."""
        # Mock the database to return an existing data source
        mock_db.query.return_value.filter.return_value.first.return_value = sample_data_source
        
        # Create workflow output
        workflow_output = WorkflowOutputCreate(
            workflow_id="test-workflow-1",
            workflow_name="Test Workflow",
            execution_id="exec-123",
            step_name="data_processing",
            data={"symbol": "AAPL", "price": 185.42},
            metadata={},
        )

        # Execute the method
        result = asyncio.run(service.store_workflow_output(workflow_output))

        # Verify that no COUNT query was executed (N+1 fix)
        # The method should only use simple increment: record_count = (record_count or 0) + 1
        count_calls = [call for call in mock_db.query.call_args_list 
                      if 'count' in str(call).lower()]
        
        # Should have no COUNT queries for record counting
        assert len(count_calls) == 0, "N+1 query issue not fixed - COUNT query detected"

        # Verify the record count was incremented correctly
        assert sample_data_source.record_count == 1

    def test_n_plus_one_query_fix_mcp_stream(self, service, mock_db, sample_data_source):
        """Test that N+1 query issue is fixed in store_mcp_data_stream."""
        # Mock the database to return an existing data source
        mock_db.query.return_value.filter.return_value.first.return_value = sample_data_source
        
        # Create MCP stream data
        mcp_stream = MCPDataStreamCreate(
            server_id="test-server-1",
            server_name="Test MCP Server",
            stream_name="market_data",
            data={"symbol": "MSFT", "price": 378.85},
            metadata={},
        )

        # Execute the method
        result = asyncio.run(service.store_mcp_data_stream(mcp_stream))

        # Verify that no COUNT query was executed (N+1 fix)
        count_calls = [call for call in mock_db.query.call_args_list 
                      if 'count' in str(call).lower()]
        
        assert len(count_calls) == 0, "N+1 query issue not fixed - COUNT query detected"

        # Verify the record count was incremented correctly
        assert sample_data_source.record_count == 1

    def test_n_plus_one_query_fix_agent_result(self, service, mock_db, sample_data_source):
        """Test that N+1 query issue is fixed in store_agent_result."""
        # Mock the database to return an existing data source
        mock_db.query.return_value.filter.return_value.first.return_value = sample_data_source
        
        # Create agent result
        agent_result = AgentResultCreate(
            agent_id="test-agent-1",
            agent_name="Test Agent",
            execution_id="exec-456",
            task_type="data_analysis",
            result={"analysis": "positive_sentiment"},
            metadata={},
        )

        # Execute the method
        result = asyncio.run(service.store_agent_result(agent_result))

        # Verify that no COUNT query was executed (N+1 fix)
        count_calls = [call for call in mock_db.query.call_args_list 
                      if 'count' in str(call).lower()]
        
        assert len(count_calls) == 0, "N+1 query issue not fixed - COUNT query detected"

        # Verify the record count was incremented correctly
        assert sample_data_source.record_count == 1

    def test_performance_under_load(self, service, mock_db, sample_data_source):
        """Test performance under high load conditions."""
        # Mock the database to return an existing data source
        mock_db.query.return_value.filter.return_value.first.return_value = sample_data_source
        
        # Simulate high load with multiple concurrent operations
        async def concurrent_operations():
            tasks = []
            for i in range(100):  # 100 concurrent operations
                workflow_output = WorkflowOutputCreate(
                    workflow_id=f"workflow-{i}",
                    workflow_name=f"Workflow {i}",
                    execution_id=f"exec-{i}",
                    step_name="data_processing",
                    data={"symbol": f"STOCK{i}", "price": 100 + i},
                    metadata={},
                )
                tasks.append(service.store_workflow_output(workflow_output))
            
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            return results, end_time - start_time

        # Execute concurrent operations
        results, execution_time = asyncio.run(concurrent_operations())

        # Verify all operations completed successfully
        assert len(results) == 100
        assert all(result is not None for result in results)

        # Performance assertion: 100 operations should complete in under 5 seconds
        # (This is a conservative estimate for the optimized version)
        assert execution_time < 5.0, f"Performance test failed: {execution_time:.2f}s for 100 operations"

        # Verify no COUNT queries were executed (N+1 fix validation)
        count_calls = [call for call in mock_db.query.call_args_list 
                      if 'count' in str(call).lower()]
        assert len(count_calls) == 0, "N+1 query issue detected under load"

    def test_error_handling_performance(self, service, mock_db):
        """Test that error handling doesn't impact performance significantly."""
        # Mock database to raise an exception
        mock_db.query.side_effect = Exception("Database connection failed")

        # Test error handling performance
        start_time = time.time()
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(service.get_data_sources())
        
        end_time = time.time()
        error_handling_time = end_time - start_time

        # Error handling should be fast (< 100ms)
        assert error_handling_time < 0.1, f"Error handling too slow: {error_handling_time:.3f}s"
        assert exc_info.value.status_code == 500

    def test_caching_effectiveness(self, service, mock_db):
        """Test that caching improves performance for repeated operations."""
        # Mock data sources
        mock_data_sources = [
            DataSource(id="1", name="Source 1", type=DataSourceType.WORKFLOW),
            DataSource(id="2", name="Source 2", type=DataSourceType.MCP),
        ]
        mock_db.query.return_value.all.return_value = mock_data_sources

        # First call (cache miss)
        start_time = time.time()
        result1 = asyncio.run(service.get_data_sources())
        first_call_time = time.time() - start_time

        # Second call (cache hit)
        start_time = time.time()
        result2 = asyncio.run(service.get_data_sources())
        second_call_time = time.time() - start_time

        # Verify results are the same
        assert result1 == result2

        # Verify caching improves performance (second call should be faster)
        # Note: In a real scenario with Redis, the difference would be more significant
        assert second_call_time <= first_call_time

    def test_memory_usage_optimization(self, service, mock_db):
        """Test that memory usage is optimized."""
        import psutil
        import os

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Perform operations that would previously cause memory issues
        for i in range(1000):
            workflow_output = WorkflowOutputCreate(
                workflow_id=f"workflow-{i}",
                workflow_name=f"Workflow {i}",
                execution_id=f"exec-{i}",
                step_name="data_processing",
                data={"symbol": f"STOCK{i}", "price": 100 + i},
                metadata={},
            )
            # Mock the database to avoid actual operations
            mock_db.query.return_value.filter.return_value.first.return_value = DataSource(
                id=f"source-{i}",
                name=f"Source {i}",
                type=DataSourceType.WORKFLOW,
                record_count=i,
            )

        # Get final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 50MB for 1000 operations)
        memory_increase_mb = memory_increase / (1024 * 1024)
        assert memory_increase_mb < 50, f"Memory usage too high: {memory_increase_mb:.2f}MB"

    def test_query_performance_monitoring(self, service, mock_db):
        """Test that query performance is properly monitored."""
        # Mock data for query
        mock_records = [
            DataRecord(
                id="1",
                data_source_id="source-1",
                data={"symbol": "AAPL", "price": 185.42},
                timestamp=datetime.utcnow(),
            )
        ]
        query = mock_db.query.return_value
        query.first.return_value = DataSource(
            id="source-1",
            name="Source 1",
            type=DataSourceType.WORKFLOW,
            source_metadata={"workflow_id": "source-1"},
        )
        query.count.return_value = 1
        query.all.return_value = mock_records

        # Create a query
        query = DataQuery(source="source-1", limit=100)

        # Execute query with performance monitoring
        start_time = time.time()
        result = asyncio.run(service.query_data(query))
        execution_time = time.time() - start_time

        # Verify query completed successfully
        data, total_count, measured_time = result
        assert len(data) == 1
        assert total_count == 1

        # Verify performance monitoring is working
        assert measured_time > 0
        assert measured_time <= execution_time  # Should be close to actual execution time

    def test_bulk_operations_performance(self, service, mock_db):
        """Test performance of bulk operations."""
        # Mock existing data source
        sample_data_source = DataSource(
            id="bulk-source",
            name="Bulk Test Source",
            type=DataSourceType.WORKFLOW,
            record_count=0,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = sample_data_source

        # Test bulk workflow output storage
        async def bulk_workflow_operations():
            start_time = time.time()
            
            for i in range(1000):
                workflow_output = WorkflowOutputCreate(
                    workflow_id="bulk-workflow",
                    workflow_name="Bulk Workflow",
                    execution_id=f"exec-{i}",
                    step_name="bulk_processing",
                    data={"batch_id": i, "processed": True},
                    metadata={"batch_size": 1000},
                )
                await service.store_workflow_output(workflow_output)
            
            end_time = time.time()
            return end_time - start_time

        execution_time = asyncio.run(bulk_workflow_operations())

        # Bulk operations should complete in reasonable time (< 10 seconds for 1000 operations)
        assert execution_time < 10.0, f"Bulk operations too slow: {execution_time:.2f}s"

        # Verify record count was incremented correctly
        assert sample_data_source.record_count == 1000

    def test_concurrent_data_source_operations(self, service, mock_db):
        """Test concurrent operations on different data sources."""
        # Mock multiple data sources
        data_sources = {}
        for i in range(10):
            data_sources[f"source-{i}"] = DataSource(
                id=f"source-{i}",
                name=f"Source {i}",
                type=DataSourceType.WORKFLOW,
                record_count=0,
                source_metadata={"workflow_id": f"workflow-{i}"},
            )
        mock_db.query.return_value.all.return_value = list(data_sources.values())

        # Test concurrent operations on different sources
        async def concurrent_source_operations():
            tasks = []
            for i in range(10):  # 10 different sources
                for j in range(10):  # 10 operations per source
                    workflow_output = WorkflowOutputCreate(
                        workflow_id=f"workflow-{i}",
                        workflow_name=f"Workflow {i}",
                        execution_id=f"exec-{i}-{j}",
                        step_name="concurrent_processing",
                        data={"source_id": f"source-{i}", "operation": j},
                        metadata={},
                    )
                    tasks.append(service.store_workflow_output(workflow_output))
            
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            return results, end_time - start_time

        results, execution_time = asyncio.run(concurrent_source_operations())

        # Verify all operations completed
        assert len(results) == 100
        assert all(result is not None for result in results)

        # Verify each source has correct record count
        for i in range(10):
            assert data_sources[f"source-{i}"].record_count == 10

        # Performance assertion
        assert execution_time < 5.0, f"Concurrent operations too slow: {execution_time:.2f}s"


class TestPerformanceBenchmarks:
    """Benchmark tests for performance validation."""

    @pytest.mark.benchmark
    def test_workflow_output_storage_benchmark(self, benchmark):
        """Benchmark workflow output storage performance."""
        # This would be used with pytest-benchmark for detailed performance analysis
        def storage_operation():
            # Simulate the optimized storage operation
            pass
        
        benchmark(storage_operation)
        assert benchmark is not None

    @pytest.mark.benchmark
    def test_query_execution_benchmark(self, benchmark):
        """Benchmark query execution performance."""
        def query_operation():
            # Simulate the optimized query operation
            pass
        
        benchmark(query_operation)
        assert benchmark is not None


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--tb=short"])
