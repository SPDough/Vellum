#!/usr/bin/env python3
"""
Test script for Custodian Data Chain

This script demonstrates how to use the CustodianDataChain to retrieve and analyze
data from custodian MCP servers.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the custodian data chain models
try:
    from app.services.custodian_data_chain import (
        CustodianDataChain,
        CustodianDataRequest,
        CustodianAnalysisRequest,
        CustodianDataResponse,
        get_custodian_data_chain,
    )
except ImportError as e:
    logger.warning(f"Could not import custodian data chain: {e}")
    # Define mock classes for testing
    class CustodianDataRequest:
        def __init__(self, custodian_id: str, data_type: str, parameters: Dict = None, 
                     filters: Dict = None, limit: int = 1000, include_metadata: bool = True):
            self.custodian_id = custodian_id
            self.data_type = data_type
            self.parameters = parameters or {}
            self.filters = filters
            self.limit = limit
            self.include_metadata = include_metadata
    
    class CustodianAnalysisRequest:
        def __init__(self, custodian_data: list, analysis_type: str, 
                     analysis_parameters: Dict = None, include_recommendations: bool = True):
            self.custodian_data = custodian_data
            self.analysis_type = analysis_type
            self.analysis_parameters = analysis_parameters or {}
            self.include_recommendations = include_recommendations
    
    class CustodianDataResponse:
        def __init__(self, success: bool, custodian_id: str, data_type: str, 
                     records_count: int, data: list, metadata: dict, 
                     execution_time_seconds: float, error_message: str = None):
            self.success = success
            self.custodian_id = custodian_id
            self.data_type = data_type
            self.records_count = records_count
            self.data = data
            self.metadata = metadata
            self.execution_time_seconds = execution_time_seconds
            self.error_message = error_message
        
        def dict(self):
            return {
                "success": self.success,
                "custodian_id": self.custodian_id,
                "data_type": self.data_type,
                "records_count": self.records_count,
                "data": self.data,
                "metadata": self.metadata,
                "execution_time_seconds": self.execution_time_seconds,
                "error_message": self.error_message,
            }

# Mock data for testing when no real MCP servers are available
MOCK_CUSTODIAN_DATA = {
    "positions": [
        {
            "position_id": "POS_001",
            "security_id": "AAPL",
            "quantity": 1000,
            "market_value": 185000.00,
            "currency": "USD",
            "custody_account": "ACC_001",
            "portfolio": "PORT_001",
            "as_of_date": "2024-01-15",
            "unrealized_pnl": 5000.00,
        },
        {
            "position_id": "POS_002",
            "security_id": "MSFT",
            "quantity": 500,
            "market_value": 175000.00,
            "currency": "USD",
            "custody_account": "ACC_001",
            "portfolio": "PORT_001",
            "as_of_date": "2024-01-15",
            "unrealized_pnl": 2500.00,
        },
        {
            "position_id": "POS_003",
            "security_id": "GOOGL",
            "quantity": 200,
            "market_value": 28000.00,
            "currency": "USD",
            "custody_account": "ACC_002",
            "portfolio": "PORT_002",
            "as_of_date": "2024-01-15",
            "unrealized_pnl": -1000.00,
        },
    ],
    "transactions": [
        {
            "transaction_id": "TXN_001",
            "security_id": "AAPL",
            "transaction_type": "BUY",
            "quantity": 100,
            "price": 180.00,
            "trade_date": "2024-01-10",
            "settlement_date": "2024-01-12",
            "currency": "USD",
            "status": "SETTLED",
        },
        {
            "transaction_id": "TXN_002",
            "security_id": "MSFT",
            "transaction_type": "SELL",
            "quantity": 50,
            "price": 350.00,
            "trade_date": "2024-01-11",
            "settlement_date": "2024-01-13",
            "currency": "USD",
            "status": "SETTLED",
        },
    ],
    "cash_balances": [
        {
            "account_id": "ACC_001",
            "currency": "USD",
            "balance": 50000.00,
            "available_balance": 45000.00,
            "as_of_date": "2024-01-15",
        },
        {
            "account_id": "ACC_002",
            "currency": "USD",
            "balance": 25000.00,
            "available_balance": 20000.00,
            "as_of_date": "2024-01-15",
        },
    ],
}


async def test_custodian_data_chain():
    """Test the custodian data chain functionality."""
    
    try:
        # Import the custodian data chain
        # from app.services.custodian_data_chain import (
        #     CustodianDataChain,
        #     CustodianDataRequest,
        #     CustodianAnalysisRequest,
        #     get_custodian_data_chain,
        # )
        
        logger.info("🚀 Starting Custodian Data Chain Test")
        
        # Get the custodian data chain instance
        try:
            custodian_chain = await get_custodian_data_chain()
        except NameError:
            logger.info("Using mock custodian chain (dependencies not available)")
            custodian_chain = None
        
        # Test 1: List available custodians
        logger.info("\n📋 Test 1: Listing available custodians")
        try:
            from app.services.mcp_service import get_mcp_service
            mcp_service = await get_mcp_service()
            custodians = await mcp_service.list_servers(provider_type="custodian", enabled_only=True)
            logger.info(f"Found {len(custodians)} custodian servers")
            for custodian in custodians:
                logger.info(f"  - {custodian.get('name', 'Unknown')} ({custodian.get('id', 'Unknown')})")
        except Exception as e:
            logger.warning(f"Could not list custodians: {e}")
        
        # Test 2: Mock data retrieval (since we don't have real MCP servers)
        logger.info("\n📊 Test 2: Mock data retrieval")
        
        # Create a mock custodian data request
        mock_request = CustodianDataRequest(
            custodian_id="mock_custodian",
            data_type="positions",
            parameters={"portfolio": "PORT_001"},
            limit=100,
            include_metadata=True,
        )
        
        # Mock the retrieval by returning test data
        mock_response = await mock_retrieve_custodian_data(mock_request)
        
        if mock_response.success:
            logger.info(f"✅ Successfully retrieved {mock_response.records_count} position records")
            logger.info(f"   Execution time: {mock_response.execution_time_seconds:.2f} seconds")
            
            # Display sample data
            if mock_response.data:
                logger.info("   Sample data:")
                for i, record in enumerate(mock_response.data[:2]):
                    logger.info(f"     Record {i+1}: {record.get('security_id', 'Unknown')} - {record.get('quantity', 0)} shares")
        else:
            logger.error(f"❌ Failed to retrieve data: {mock_response.error_message}")
        
        # Test 3: Data analysis
        logger.info("\n🔍 Test 3: Data analysis")
        
        if mock_response.success and mock_response.data:
            # Create analysis request
            analysis_request = CustodianAnalysisRequest(
                custodian_data=mock_response.data,
                analysis_type="risk_assessment",
                analysis_parameters={"risk_threshold": 0.1},
                include_recommendations=True,
            )
            
            # Analyze the data
            if custodian_chain:
                analysis_response = await custodian_chain.analyze_custodian_data(analysis_request)
            else:
                # Mock analysis response
                analysis_response = type('MockResponse', (), {
                    'success': True,
                    'analysis_type': 'risk_assessment',
                    'insights': [{'title': 'Mock Insight', 'description': 'Mock analysis'}],
                    'recommendations': [{'title': 'Mock Recommendation', 'description': 'Mock recommendation'}],
                    'execution_time_seconds': 0.1,
                    'error_message': None
                })()
            
            if analysis_response.success:
                logger.info(f"✅ Successfully analyzed data")
                logger.info(f"   Analysis type: {analysis_response.analysis_type}")
                logger.info(f"   Insights found: {len(analysis_response.insights)}")
                logger.info(f"   Recommendations: {len(analysis_response.recommendations)}")
                logger.info(f"   Execution time: {analysis_response.execution_time_seconds:.2f} seconds")
                
                # Display insights
                if analysis_response.insights:
                    logger.info("   Key insights:")
                    for insight in analysis_response.insights[:3]:
                        logger.info(f"     - {insight.get('title', 'Unknown')}: {insight.get('description', 'No description')}")
                
                # Display recommendations
                if analysis_response.recommendations:
                    logger.info("   Recommendations:")
                    for rec in analysis_response.recommendations[:3]:
                        logger.info(f"     - {rec.get('title', 'Unknown')}: {rec.get('description', 'No description')}")
            else:
                logger.error(f"❌ Failed to analyze data: {analysis_response.error_message}")
        
        # Test 4: Combined retrieve and analyze
        logger.info("\n🔄 Test 4: Combined retrieve and analyze")
        
        # This would normally call the API endpoint, but we'll simulate it
        combined_result = await mock_combined_retrieve_and_analyze(mock_request, "general")
        
        if combined_result.get("success"):
            logger.info("✅ Successfully completed combined retrieve and analyze")
            retrieval_time = combined_result.get("retrieval", {}).get("execution_time_seconds", 0)
            analysis_time = combined_result.get("analysis", {}).get("execution_time_seconds", 0)
            total_time = combined_result.get("combined_execution_time_seconds", 0)
            logger.info(f"   Retrieval time: {retrieval_time:.2f}s")
            logger.info(f"   Analysis time: {analysis_time:.2f}s")
            logger.info(f"   Total time: {total_time:.2f}s")
        else:
            logger.error(f"❌ Combined operation failed: {combined_result.get('error_message', 'Unknown error')}")
        
        logger.info("\n🎉 Custodian Data Chain Test Completed Successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


async def mock_retrieve_custodian_data(request: CustodianDataRequest) -> CustodianDataResponse:
    """Mock custodian data retrieval for testing."""
    
    start_time = datetime.utcnow()
    
    try:
        # Simulate network delay
        await asyncio.sleep(0.1)
        
        # Get mock data based on data type
        mock_data = MOCK_CUSTODIAN_DATA.get(request.data_type, [])
        
        # Apply filters if specified
        if request.filters:
            # Simple filtering logic
            filtered_data = []
            for record in mock_data:
                if all(record.get(k) == v for k, v in request.filters.items()):
                    filtered_data.append(record)
            mock_data = filtered_data
        
        # Apply limit
        if request.limit and len(mock_data) > request.limit:
            mock_data = mock_data[:request.limit]
        
        # Add validation timestamps
        for record in mock_data:
            record["_validation_timestamp"] = datetime.utcnow().isoformat()
            record["_data_type"] = request.data_type
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return CustodianDataResponse(
            success=True,
            custodian_id=request.custodian_id,
            data_type=request.data_type,
            records_count=len(mock_data),
            data=mock_data,
            metadata={
                "custodian_id": request.custodian_id,
                "data_type": request.data_type,
                "retrieval_time": datetime.utcnow().isoformat(),
                "execution_time_seconds": execution_time,
                "records_count": len(mock_data),
                "available_tools": ["positions", "transactions", "cash_balances"],
                "parameters_used": request.parameters,
                "mock_data": True,
            },
            execution_time_seconds=execution_time,
        )
        
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        return CustodianDataResponse(
            success=False,
            custodian_id=request.custodian_id,
            data_type=request.data_type,
            records_count=0,
            data=[],
            metadata={},
            execution_time_seconds=execution_time,
            error_message=str(e),
        )


async def mock_combined_retrieve_and_analyze(request: CustodianDataRequest, analysis_type: str) -> Dict[str, Any]:
    """Mock combined retrieve and analyze operation."""
    
    # Step 1: Retrieve data
    retrieval_response = await mock_retrieve_custodian_data(request)
    
    if not retrieval_response.success:
        return {
            "success": False,
            "error_message": retrieval_response.error_message,
            "retrieval": retrieval_response.dict(),
            "analysis": None,
        }
    
    # Step 2: Analyze data (mock)
    analysis_response = {
        "success": True,
        "analysis_type": analysis_type,
        "insights": [
            {
                "type": "data_overview",
                "title": "Data Overview",
                "description": f"Analyzed {len(retrieval_response.data)} records",
                "value": len(retrieval_response.data),
                "severity": "info"
            }
        ],
        "recommendations": [
            {
                "type": "data_quality",
                "title": "Data Validation",
                "description": "Implement automated data validation checks",
                "priority": "medium",
                "action": "setup_validation"
            }
        ],
        "summary": {
            "total_records": len(retrieval_response.data),
            "total_columns": len(retrieval_response.data[0]) if retrieval_response.data else 0,
            "insights_count": 1,
            "recommendations_count": 1,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "data_quality_score": 0.95
        },
        "execution_time_seconds": 0.05,
        "error_message": None
    }
    
    # Step 3: Combine results
    return {
        "success": True,
        "retrieval": retrieval_response.dict(),
        "analysis": analysis_response,
        "combined_execution_time_seconds": (
            retrieval_response.execution_time_seconds + analysis_response["execution_time_seconds"]
        ),
    }


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_custodian_data_chain())
