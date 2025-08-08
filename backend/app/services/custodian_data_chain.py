"""
Custodian Data Chain Service for Otomeshon Platform

This service provides LangChain chains for pulling and processing data from custodian MCP servers.
It integrates with the existing MCP service infrastructure to provide a unified interface for
custodian data access and analysis.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from langchain.agents import AgentExecutor, create_pandas_dataframe_agent
from langchain.agents.agent_types import AgentType
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.schema.runnable import Runnable, RunnableSequence
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.services.mcp_service import MCPService, MCPServerType, get_mcp_service

logger = logging.getLogger(__name__)
settings = get_settings()


class CustodianDataRequest(BaseModel):
    """Request model for custodian data retrieval."""
    
    custodian_id: str = Field(..., description="ID of the custodian MCP server")
    data_type: str = Field(..., description="Type of data to retrieve (positions, transactions, cash_balances, etc.)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the data request")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Filters to apply to the data")
    limit: Optional[int] = Field(default=1000, description="Maximum number of records to retrieve")
    include_metadata: bool = Field(default=True, description="Whether to include metadata in the response")


class CustodianDataResponse(BaseModel):
    """Response model for custodian data retrieval."""
    
    success: bool
    custodian_id: str
    data_type: str
    records_count: int
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    execution_time_seconds: float
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class CustodianAnalysisRequest(BaseModel):
    """Request model for custodian data analysis."""
    
    custodian_data: List[Dict[str, Any]]
    analysis_type: str = Field(..., description="Type of analysis to perform")
    analysis_parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the analysis")
    include_recommendations: bool = Field(default=True, description="Whether to include recommendations")


class CustodianAnalysisResponse(BaseModel):
    """Response model for custodian data analysis."""
    
    success: bool
    analysis_type: str
    insights: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    summary: Dict[str, Any]
    execution_time_seconds: float
    error_message: Optional[str] = None


class CustodianDataChain:
    """
    LangChain chain for pulling and processing custodian data.
    
    This chain provides:
    1. Data retrieval from custodian MCP servers
    2. Data validation and transformation
    3. Automated analysis and insights
    4. Integration with the data sandbox
    """
    
    def __init__(self, mcp_service: Optional[MCPService] = None, llm: Any = None):
        self.mcp_service = mcp_service
        self.llm = llm
        self._setup_llm()
        self._setup_chains()
    
    def _setup_llm(self):
        """Setup the LLM for the chain."""
        if not self.llm:
            if settings.anthropic_api_key:
                self.llm = ChatAnthropic(
                    model="claude-3-haiku-20240307",
                    api_key=settings.anthropic_api_key,
                    temperature=0.1,
                )
            elif settings.openai_api_key:
                self.llm = ChatOpenAI(
                    model="gpt-3.5-turbo",
                    api_key=settings.openai_api_key,
                    temperature=0.1,
                )
            else:
                logger.warning("No LLM API keys configured - using mock responses")
                self.llm = None
    
    def _setup_chains(self):
        """Setup the LangChain chains."""
        # Data retrieval chain
        self.data_retrieval_chain = self._create_data_retrieval_chain()
        
        # Data analysis chain
        self.data_analysis_chain = self._create_data_analysis_chain()
        
        # Data validation chain
        self.data_validation_chain = self._create_data_validation_chain()
        
        # Data transformation chain
        self.data_transformation_chain = self._create_data_transformation_chain()
    
    def _create_data_retrieval_chain(self) -> RunnableSequence:
        """Create a chain for retrieving data from custodian MCP servers."""
        
        # System prompt for data retrieval
        system_prompt = """You are a custodian data retrieval specialist. Your role is to:
1. Understand the data request requirements
2. Format the request appropriately for the custodian MCP server
3. Handle errors and retries gracefully
4. Validate the retrieved data
5. Provide clear feedback on the retrieval process

Guidelines:
- Always validate the custodian server is available before making requests
- Handle authentication and authorization appropriately
- Provide detailed error messages if retrieval fails
- Ensure data is properly formatted and validated
- Include metadata about the retrieval process"""

        # Human prompt template
        human_prompt = """Retrieve {data_type} data from custodian {custodian_id}.

Parameters: {parameters}
Filters: {filters}
Limit: {limit}

Please:
1. Check if the custodian server is available
2. Retrieve the requested data
3. Validate the data format and content
4. Return the data with appropriate metadata"""

        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])
        
        # Create the chain
        if self.llm:
            chain = prompt | self.llm
        else:
            # Mock chain for when no LLM is available
            chain = self._mock_data_retrieval_chain()
        
        return chain
    
    def _create_data_analysis_chain(self) -> RunnableSequence:
        """Create a chain for analyzing custodian data."""
        
        system_prompt = """You are a custodian data analyst specializing in banking operations. Your role is to:
1. Analyze custodian data for insights and patterns
2. Identify potential risks and anomalies
3. Provide actionable recommendations
4. Generate summary statistics and metrics
5. Ensure compliance with banking regulations

Guidelines:
- Focus on actionable insights
- Consider risk management implications
- Provide specific, measurable recommendations
- Include relevant metrics and statistics
- Consider regulatory compliance requirements"""

        human_prompt = """Analyze the following custodian data:

Data Type: {data_type}
Records Count: {records_count}
Data Sample: {data_sample}

Analysis Type: {analysis_type}
Parameters: {analysis_parameters}

Please provide:
1. Key insights and patterns
2. Risk assessment
3. Compliance notes
4. Recommendations
5. Summary statistics"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])
        
        if self.llm:
            chain = prompt | self.llm
        else:
            chain = self._mock_data_analysis_chain()
        
        return chain
    
    def _create_data_validation_chain(self) -> RunnableSequence:
        """Create a chain for validating custodian data."""
        
        system_prompt = """You are a data validation specialist for custodian banking data. Your role is to:
1. Validate data completeness and accuracy
2. Check for data quality issues
3. Identify missing or invalid fields
4. Ensure data format compliance
5. Provide validation reports

Guidelines:
- Check for required fields
- Validate data types and formats
- Identify outliers and anomalies
- Ensure data consistency
- Provide detailed validation feedback"""

        human_prompt = """Validate the following custodian data:

Data Type: {data_type}
Records Count: {records_count}
Data Sample: {data_sample}

Please provide:
1. Data quality assessment
2. Missing or invalid fields
3. Outliers and anomalies
4. Validation recommendations
5. Overall data quality score"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])
        
        if self.llm:
            chain = prompt | self.llm
        else:
            chain = self._mock_data_validation_chain()
        
        return chain
    
    def _create_data_transformation_chain(self) -> RunnableSequence:
        """Create a chain for transforming custodian data."""
        
        system_prompt = """You are a data transformation specialist for custodian banking data. Your role is to:
1. Transform data into standardized formats
2. Apply business rules and calculations
3. Handle data type conversions
4. Ensure data consistency
5. Provide transformation logs

Guidelines:
- Maintain data integrity during transformations
- Apply business rules consistently
- Handle edge cases and errors
- Provide clear transformation logs
- Ensure output format compliance"""

        human_prompt = """Transform the following custodian data:

Data Type: {data_type}
Records Count: {records_count}
Data Sample: {data_sample}

Transformation Rules: {transformation_rules}

Please provide:
1. Transformed data
2. Transformation logs
3. Applied business rules
4. Data quality metrics
5. Transformation summary"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])
        
        if self.llm:
            chain = prompt | self.llm
        else:
            chain = self._mock_data_transformation_chain()
        
        return chain
    
    async def retrieve_custodian_data(self, request: CustodianDataRequest) -> CustodianDataResponse:
        """
        Retrieve data from a custodian MCP server.
        
        Args:
            request: CustodianDataRequest containing the retrieval parameters
            
        Returns:
            CustodianDataResponse with the retrieved data and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            # Get MCP service if not provided
            if not self.mcp_service:
                self.mcp_service = await get_mcp_service()
            
            # Check if custodian server exists and is available
            custodian_info = await self.mcp_service.get_server(request.custodian_id)
            if not custodian_info:
                raise ValueError(f"Custodian server {request.custodian_id} not found")
            
            if not custodian_info.get("enabled", False):
                raise ValueError(f"Custodian server {request.custodian_id} is not enabled")
            
            # Test connection to custodian server
            connection_test = await self.mcp_service.test_server_connection(request.custodian_id)
            if not connection_test.get("success", False):
                raise ValueError(f"Cannot connect to custodian server {request.custodian_id}: {connection_test.get('error_message', 'Unknown error')}")
            
            # Get available tools for the custodian
            capabilities = await self.mcp_service.get_server_capabilities(request.custodian_id)
            available_tools = [tool.get("name", "") for tool in capabilities]
            
            # Check if requested data type is available
            if request.data_type not in available_tools:
                raise ValueError(f"Data type {request.data_type} not available for custodian {request.custodian_id}. Available: {available_tools}")
            
            # Call the custodian MCP server
            logger.info(f"Retrieving {request.data_type} data from custodian {request.custodian_id}")
            
            # Prepare parameters for the MCP call
            mcp_parameters = {
                **request.parameters,
                "limit": request.limit,
            }
            
            if request.filters:
                mcp_parameters["filters"] = request.filters
            
            # Make the actual call to the custodian
            raw_response = await self.mcp_service.call_tool(
                request.custodian_id,
                request.data_type,
                mcp_parameters
            )
            
            # Process the response
            if isinstance(raw_response, dict) and "data" in raw_response:
                data = raw_response["data"]
            elif isinstance(raw_response, list):
                data = raw_response
            else:
                data = [raw_response] if raw_response else []
            
            # Validate and transform the data
            validated_data = await self._validate_custodian_data(data, request.data_type)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Prepare metadata
            metadata = {
                "custodian_id": request.custodian_id,
                "data_type": request.data_type,
                "retrieval_time": datetime.utcnow().isoformat(),
                "execution_time_seconds": execution_time,
                "records_count": len(validated_data),
                "available_tools": available_tools,
                "parameters_used": mcp_parameters,
            }
            
            if request.include_metadata:
                metadata["raw_response"] = raw_response
            
            return CustodianDataResponse(
                success=True,
                custodian_id=request.custodian_id,
                data_type=request.data_type,
                records_count=len(validated_data),
                data=validated_data,
                metadata=metadata,
                execution_time_seconds=execution_time,
                raw_response=raw_response if request.include_metadata else None
            )
            
        except Exception as e:
            logger.error(f"Error retrieving custodian data: {str(e)}")
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return CustodianDataResponse(
                success=False,
                custodian_id=request.custodian_id,
                data_type=request.data_type,
                records_count=0,
                data=[],
                metadata={},
                execution_time_seconds=execution_time,
                error_message=str(e)
            )
    
    async def analyze_custodian_data(self, request: CustodianAnalysisRequest) -> CustodianAnalysisResponse:
        """
        Analyze custodian data using LangChain.
        
        Args:
            request: CustodianAnalysisRequest containing the analysis parameters
            
        Returns:
            CustodianAnalysisResponse with analysis results
        """
        start_time = datetime.utcnow()
        
        try:
            if not request.custodian_data:
                raise ValueError("No custodian data provided for analysis")
            
            # Convert data to DataFrame for analysis
            df = pd.DataFrame(request.custodian_data)
            
            # Prepare analysis parameters
            analysis_params = {
                "data_type": "custodian_data",
                "records_count": len(df),
                "data_sample": df.head(5).to_dict("records"),
                "analysis_type": request.analysis_type,
                "analysis_parameters": request.analysis_parameters
            }
            
            # Run the analysis chain
            if self.llm:
                analysis_result = await asyncio.to_thread(
                    self.data_analysis_chain.invoke,
                    analysis_params
                )
                
                # Parse the analysis result
                analysis_content = analysis_result.content if hasattr(analysis_result, 'content') else str(analysis_result)
                
                # Extract insights and recommendations
                insights = self._extract_insights_from_analysis(analysis_content, df)
                recommendations = self._extract_recommendations_from_analysis(analysis_content) if request.include_recommendations else []
                summary = self._create_analysis_summary(df, insights, recommendations)
                
            else:
                # Mock analysis when no LLM is available
                insights = self._mock_insights(df)
                recommendations = self._mock_recommendations() if request.include_recommendations else []
                summary = self._create_analysis_summary(df, insights, recommendations)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return CustodianAnalysisResponse(
                success=True,
                analysis_type=request.analysis_type,
                insights=insights,
                recommendations=recommendations,
                summary=summary,
                execution_time_seconds=execution_time
            )
            
        except Exception as e:
            logger.error(f"Error analyzing custodian data: {str(e)}")
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return CustodianAnalysisResponse(
                success=False,
                analysis_type=request.analysis_type,
                insights=[],
                recommendations=[],
                summary={},
                execution_time_seconds=execution_time,
                error_message=str(e)
            )
    
    async def _validate_custodian_data(self, data: List[Dict[str, Any]], data_type: str) -> List[Dict[str, Any]]:
        """Validate custodian data."""
        if not data:
            return []
        
        validated_data = []
        
        for record in data:
            # Basic validation - ensure record is a dictionary
            if not isinstance(record, dict):
                logger.warning(f"Skipping invalid record: {record}")
                continue
            
            # Add validation timestamp
            record["_validation_timestamp"] = datetime.utcnow().isoformat()
            record["_data_type"] = data_type
            
            validated_data.append(record)
        
        return validated_data
    
    def _extract_insights_from_analysis(self, analysis_content: str, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract insights from analysis content."""
        insights = []
        
        # Basic insights based on data characteristics
        if not df.empty:
            insights.append({
                "type": "data_overview",
                "title": "Data Overview",
                "description": f"Analyzed {len(df)} records with {len(df.columns)} columns",
                "value": len(df),
                "severity": "info"
            })
            
            # Check for missing data
            missing_data = df.isnull().sum().sum()
            if missing_data > 0:
                insights.append({
                    "type": "data_quality",
                    "title": "Missing Data",
                    "description": f"Found {missing_data} missing values across the dataset",
                    "value": missing_data,
                    "severity": "warning"
                })
            
            # Check for duplicates
            duplicates = df.duplicated().sum()
            if duplicates > 0:
                insights.append({
                    "type": "data_quality",
                    "title": "Duplicate Records",
                    "description": f"Found {duplicates} duplicate records",
                    "value": duplicates,
                    "severity": "warning"
                })
        
        return insights
    
    def _extract_recommendations_from_analysis(self, analysis_content: str) -> List[Dict[str, Any]]:
        """Extract recommendations from analysis content."""
        # This would be enhanced with LLM parsing in a real implementation
        return [
            {
                "type": "data_quality",
                "title": "Data Validation",
                "description": "Implement automated data validation checks",
                "priority": "medium",
                "action": "setup_validation"
            }
        ]
    
    def _create_analysis_summary(self, df: pd.DataFrame, insights: List[Dict[str, Any]], recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of the analysis."""
        return {
            "total_records": len(df),
            "total_columns": len(df.columns) if not df.empty else 0,
            "insights_count": len(insights),
            "recommendations_count": len(recommendations),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "data_quality_score": self._calculate_data_quality_score(df)
        }
    
    def _calculate_data_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate a data quality score."""
        if df.empty:
            return 0.0
        
        # Simple quality score based on missing data and duplicates
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        duplicate_rows = df.duplicated().sum()
        
        quality_score = 1.0 - (missing_cells / total_cells) - (duplicate_rows / len(df))
        return max(0.0, min(1.0, quality_score))
    
    # Mock methods for when LLM is not available
    def _mock_data_retrieval_chain(self):
        """Mock data retrieval chain."""
        return lambda x: {"content": f"Mock retrieval for {x.get('data_type', 'unknown')} data"}
    
    def _mock_data_analysis_chain(self):
        """Mock data analysis chain."""
        return lambda x: {"content": f"Mock analysis for {x.get('analysis_type', 'unknown')} analysis"}
    
    def _mock_data_validation_chain(self):
        """Mock data validation chain."""
        return lambda x: {"content": f"Mock validation for {x.get('data_type', 'unknown')} data"}
    
    def _mock_data_transformation_chain(self):
        """Mock data transformation chain."""
        return lambda x: {"content": f"Mock transformation for {x.get('data_type', 'unknown')} data"}
    
    def _mock_insights(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Mock insights for testing."""
        return [
            {
                "type": "mock_insight",
                "title": "Mock Data Insight",
                "description": f"Mock insight for {len(df)} records",
                "value": len(df),
                "severity": "info"
            }
        ]
    
    def _mock_recommendations(self) -> List[Dict[str, Any]]:
        """Mock recommendations for testing."""
        return [
            {
                "type": "mock_recommendation",
                "title": "Mock Recommendation",
                "description": "This is a mock recommendation for testing",
                "priority": "low",
                "action": "mock_action"
            }
        ]


# Global service instance
_custodian_data_chain = None


async def get_custodian_data_chain() -> CustodianDataChain:
    """Dependency injection for custodian data chain."""
    global _custodian_data_chain
    if _custodian_data_chain is None:
        mcp_service = await get_mcp_service()
        _custodian_data_chain = CustodianDataChain(mcp_service=mcp_service)
    return _custodian_data_chain
