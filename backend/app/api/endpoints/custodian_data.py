"""
Custodian Data API Endpoints for Otomeshon Platform

Provides REST API endpoints for retrieving and analyzing data from custodian MCP servers
using LangChain chains.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.endpoints.auth_unified import get_current_user
from app.models.user import User
from app.services.custodian_data_chain import (
    CustodianAnalysisRequest,
    CustodianAnalysisResponse,
    CustodianDataRequest,
    CustodianDataResponse,
    get_custodian_data_chain,
)

router = APIRouter(prefix="/custodian-data", tags=["Custodian Data"])


class CustodianDataRetrievalRequest(BaseModel):
    """Request model for custodian data retrieval via API."""
    
    custodian_id: str = Field(..., description="ID of the custodian MCP server")
    data_type: str = Field(..., description="Type of data to retrieve (positions, transactions, cash_balances, etc.)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the data request")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Filters to apply to the data")
    limit: Optional[int] = Field(default=1000, ge=1, le=10000, description="Maximum number of records to retrieve")
    include_metadata: bool = Field(default=True, description="Whether to include metadata in the response")


class CustodianDataAnalysisRequest(BaseModel):
    """Request model for custodian data analysis via API."""
    
    custodian_data: List[Dict[str, Any]] = Field(..., description="Custodian data to analyze")
    analysis_type: str = Field(..., description="Type of analysis to perform")
    analysis_parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the analysis")
    include_recommendations: bool = Field(default=True, description="Whether to include recommendations")


class CustodianDataRetrievalResponse(BaseModel):
    """Response model for custodian data retrieval via API."""
    
    success: bool
    custodian_id: str
    data_type: str
    records_count: int
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    execution_time_seconds: float
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class CustodianDataAnalysisResponse(BaseModel):
    """Response model for custodian data analysis via API."""
    
    success: bool
    analysis_type: str
    insights: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    summary: Dict[str, Any]
    execution_time_seconds: float
    error_message: Optional[str] = None


@router.post("/retrieve", response_model=CustodianDataRetrievalResponse)
async def retrieve_custodian_data(
    request: CustodianDataRetrievalRequest,
    current_user: User = Depends(get_current_user),
    custodian_chain = Depends(get_custodian_data_chain),
) -> CustodianDataRetrievalResponse:
    """
    Retrieve data from a custodian MCP server using LangChain.
    
    This endpoint:
    1. Validates the custodian server is available
    2. Retrieves the requested data type
    3. Validates and transforms the data
    4. Returns the data with metadata
    """
    try:
        # Convert API request to internal request model
        internal_request = CustodianDataRequest(
            custodian_id=request.custodian_id,
            data_type=request.data_type,
            parameters=request.parameters,
            filters=request.filters,
            limit=request.limit,
            include_metadata=request.include_metadata,
        )
        
        # Retrieve the data
        response = await custodian_chain.retrieve_custodian_data(internal_request)
        
        # Convert to API response model
        return CustodianDataRetrievalResponse(
            success=response.success,
            custodian_id=response.custodian_id,
            data_type=response.data_type,
            records_count=response.records_count,
            data=response.data,
            metadata=response.metadata,
            execution_time_seconds=response.execution_time_seconds,
            error_message=response.error_message,
            raw_response=response.raw_response,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve custodian data: {str(e)}",
        )


@router.post("/analyze", response_model=CustodianDataAnalysisResponse)
async def analyze_custodian_data(
    request: CustodianDataAnalysisRequest,
    current_user: User = Depends(get_current_user),
    custodian_chain = Depends(get_custodian_data_chain),
) -> CustodianDataAnalysisResponse:
    """
    Analyze custodian data using LangChain.
    
    This endpoint:
    1. Takes custodian data as input
    2. Performs analysis using LangChain
    3. Extracts insights and recommendations
    4. Returns analysis results
    """
    try:
        # Convert API request to internal request model
        internal_request = CustodianAnalysisRequest(
            custodian_data=request.custodian_data,
            analysis_type=request.analysis_type,
            analysis_parameters=request.analysis_parameters,
            include_recommendations=request.include_recommendations,
        )
        
        # Analyze the data
        response = await custodian_chain.analyze_custodian_data(internal_request)
        
        # Convert to API response model
        return CustodianDataAnalysisResponse(
            success=response.success,
            analysis_type=response.analysis_type,
            insights=response.insights,
            recommendations=response.recommendations,
            summary=response.summary,
            execution_time_seconds=response.execution_time_seconds,
            error_message=response.error_message,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze custodian data: {str(e)}",
        )


@router.get("/custodians", response_model=List[Dict[str, Any]])
async def list_available_custodians(
    current_user: User = Depends(get_current_user),
    custodian_chain = Depends(get_custodian_data_chain),
) -> List[Dict[str, Any]]:
    """
    List available custodian MCP servers.
    
    Returns a list of all available custodian servers with their capabilities.
    """
    try:
        # Get MCP service from the chain
        mcp_service = custodian_chain.mcp_service
        if not mcp_service:
            mcp_service = await get_custodian_data_chain()
            mcp_service = mcp_service.mcp_service
        
        # List all custodian servers
        servers = await mcp_service.list_servers(provider_type="custodian", enabled_only=True)
        
        # Format the response
        formatted_servers = []
        for server in servers:
            formatted_server = {
                "id": server.get("id"),
                "name": server.get("name"),
                "type": server.get("type"),
                "status": server.get("status", "unknown"),
                "capabilities": server.get("capabilities", []),
                "enabled": server.get("enabled", False),
                "last_health_check": server.get("last_health_check"),
            }
            formatted_servers.append(formatted_server)
        
        return formatted_servers
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list custodians: {str(e)}",
        )


@router.get("/custodians/{custodian_id}/capabilities", response_model=List[Dict[str, Any]])
async def get_custodian_capabilities(
    custodian_id: str,
    current_user: User = Depends(get_current_user),
    custodian_chain = Depends(get_custodian_data_chain),
) -> List[Dict[str, Any]]:
    """
    Get capabilities of a specific custodian MCP server.
    
    Returns the available tools and capabilities for the specified custodian.
    """
    try:
        # Get MCP service from the chain
        mcp_service = custodian_chain.mcp_service
        if not mcp_service:
            mcp_service = await get_custodian_data_chain()
            mcp_service = mcp_service.mcp_service
        
        # Get capabilities for the specific custodian
        capabilities = await mcp_service.get_server_capabilities(custodian_id)
        
        return capabilities
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get custodian capabilities: {str(e)}",
        )


@router.get("/custodians/{custodian_id}/health", response_model=Dict[str, Any])
async def get_custodian_health(
    custodian_id: str,
    current_user: User = Depends(get_current_user),
    custodian_chain = Depends(get_custodian_data_chain),
) -> Dict[str, Any]:
    """
    Get health status of a specific custodian MCP server.
    
    Returns the current health status and metrics for the specified custodian.
    """
    try:
        # Get MCP service from the chain
        mcp_service = custodian_chain.mcp_service
        if not mcp_service:
            mcp_service = await get_custodian_data_chain()
            mcp_service = mcp_service.mcp_service
        
        # Test connection to the custodian
        health_status = await mcp_service.test_server_connection(custodian_id)
        
        # Get additional metrics if available
        try:
            metrics = await mcp_service.get_server_metrics(custodian_id)
            health_status["metrics"] = metrics
        except Exception:
            health_status["metrics"] = {}
        
        return health_status
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get custodian health: {str(e)}",
        )


@router.post("/retrieve-and-analyze", response_model=Dict[str, Any])
async def retrieve_and_analyze_custodian_data(
    retrieval_request: CustodianDataRetrievalRequest,
    analysis_type: str = Query(default="general", description="Type of analysis to perform"),
    analysis_parameters: Dict[str, Any] = Query(default_factory=dict, description="Parameters for the analysis"),
    include_recommendations: bool = Query(default=True, description="Whether to include recommendations"),
    current_user: User = Depends(get_current_user),
    custodian_chain = Depends(get_custodian_data_chain),
) -> Dict[str, Any]:
    """
    Retrieve and analyze custodian data in a single operation.
    
    This endpoint combines data retrieval and analysis for convenience.
    """
    try:
        # Step 1: Retrieve the data
        retrieval_response = await retrieve_custodian_data(
            retrieval_request, current_user, custodian_chain
        )
        
        if not retrieval_response.success:
            return {
                "success": False,
                "error_message": retrieval_response.error_message,
                "retrieval": retrieval_response.dict(),
                "analysis": None,
            }
        
        # Step 2: Analyze the data
        analysis_request = CustodianDataAnalysisRequest(
            custodian_data=retrieval_response.data,
            analysis_type=analysis_type,
            analysis_parameters=analysis_parameters,
            include_recommendations=include_recommendations,
        )
        
        analysis_response = await analyze_custodian_data(
            analysis_request, current_user, custodian_chain
        )
        
        # Step 3: Combine the results
        return {
            "success": True,
            "retrieval": retrieval_response.dict(),
            "analysis": analysis_response.dict(),
            "combined_execution_time_seconds": (
                retrieval_response.execution_time_seconds + analysis_response.execution_time_seconds
            ),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve and analyze custodian data: {str(e)}",
        )


@router.get("/data-types", response_model=List[str])
async def get_available_data_types(
    current_user: User = Depends(get_current_user),
) -> List[str]:
    """
    Get list of available data types for custodian data retrieval.
    
    Returns a list of common data types that can be retrieved from custodians.
    """
    return [
        "positions",
        "transactions",
        "cash_balances",
        "holdings",
        "trades",
        "settlements",
        "corporate_actions",
        "reference_data",
        "market_data",
        "risk_metrics",
        "compliance_data",
        "performance_data",
    ]


@router.get("/analysis-types", response_model=List[str])
async def get_available_analysis_types(
    current_user: User = Depends(get_current_user),
) -> List[str]:
    """
    Get list of available analysis types for custodian data.
    
    Returns a list of analysis types that can be performed on custodian data.
    """
    return [
        "general",
        "risk_assessment",
        "compliance_check",
        "performance_analysis",
        "data_quality",
        "anomaly_detection",
        "trend_analysis",
        "concentration_analysis",
        "liquidity_analysis",
        "volatility_analysis",
    ]
