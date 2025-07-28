from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.data_source_service import DataSourceService
from app.services.langchain_data_workflow_service import LangchainDataWorkflowService

router = APIRouter(prefix="/data-workflows", tags=["data-workflows"])


class WorkflowExecutionRequest(BaseModel):
    """Request model for executing data workflows."""
    
    source_config_id: str
    workflow_prompt: str
    custom_instructions: Optional[str] = None
    use_docker_repl: bool = True  # Use secure Docker REPL by default


class SQLWorkflowRequest(BaseModel):
    """Request model for SQL workflows."""
    
    connection_string: str
    query_prompt: str
    table_names: Optional[List[str]] = None


class DataPipelineRequest(BaseModel):
    """Request model for data pipeline workflows."""
    
    source_config_ids: List[str]
    pipeline_instructions: str
    output_format: str = "dataframe"


class AutoInsightsRequest(BaseModel):
    """Request model for automated insights."""
    
    source_config_id: str
    insight_type: str = "general"


def get_workflow_service(db: AsyncSession = Depends(get_db)) -> LangchainDataWorkflowService:
    """Get Langchain workflow service instance."""
    data_source_service = DataSourceService(db)
    # In production, get OpenAI API key from environment or config
    openai_api_key = "your-openai-api-key"  # Replace with actual key management
    return LangchainDataWorkflowService(data_source_service, openai_api_key)


@router.post("/execute")
async def execute_data_workflow(
    request: WorkflowExecutionRequest,
    service: LangchainDataWorkflowService = Depends(get_workflow_service)
) -> Dict:
    """Execute a data workflow using Langchain agents."""
    try:
        # Get data source configuration
        config = await service.data_source_service.get_configuration(request.source_config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Data source configuration not found")
        
        # Execute workflow (choose method based on request)
        if request.use_docker_repl:
            result = await service.execute_data_workflow_with_docker_repl(
                config=config,
                workflow_prompt=request.workflow_prompt,
                custom_instructions=request.custom_instructions
            )
        else:
            result = await service.execute_data_workflow(
                config=config,
                workflow_prompt=request.workflow_prompt,
                custom_instructions=request.custom_instructions
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")


@router.post("/sql")
async def execute_sql_workflow(
    request: SQLWorkflowRequest,
    service: LangchainDataWorkflowService = Depends(get_workflow_service)
) -> Dict:
    """Execute a SQL-based workflow using Langchain SQL agent."""
    try:
        result = await service.create_sql_workflow(
            connection_string=request.connection_string,
            query_prompt=request.query_prompt,
            table_names=request.table_names
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute SQL workflow: {str(e)}")


@router.post("/pipeline")
async def execute_data_pipeline(
    request: DataPipelineRequest,
    service: LangchainDataWorkflowService = Depends(get_workflow_service)
) -> Dict:
    """Execute a data pipeline workflow with multiple sources."""
    try:
        # Get all source configurations
        source_configs = []
        for config_id in request.source_config_ids:
            config = await service.data_source_service.get_configuration(config_id)
            if not config:
                raise HTTPException(status_code=404, detail=f"Data source configuration {config_id} not found")
            source_configs.append(config)
        
        # Execute pipeline workflow
        result = await service.create_data_pipeline_workflow(
            source_configs=source_configs,
            pipeline_instructions=request.pipeline_instructions,
            output_format=request.output_format
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute pipeline workflow: {str(e)}")


@router.post("/insights")
async def generate_automated_insights(
    request: AutoInsightsRequest,
    service: LangchainDataWorkflowService = Depends(get_workflow_service)
) -> Dict:
    """Generate automated insights from a data source."""
    try:
        # Get data source configuration
        config = await service.data_source_service.get_configuration(request.source_config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Data source configuration not found")
        
        # Generate insights
        result = await service.create_automated_insights_workflow(
            config=config,
            insight_type=request.insight_type
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@router.get("/templates")
async def get_workflow_templates() -> Dict:
    """Get predefined workflow templates."""
    templates = {
        "data_analysis": {
            "name": "Data Analysis",
            "description": "Comprehensive analysis of dataset including statistics, patterns, and insights",
            "prompt": "Analyze this dataset and provide insights on data quality, statistical summary, key patterns, and recommendations for improvement.",
            "category": "analysis"
        },
        "anomaly_detection": {
            "name": "Anomaly Detection",
            "description": "Detect outliers and anomalies in the data",
            "prompt": "Identify anomalies, outliers, and unusual patterns in this dataset. Provide explanations for detected anomalies and suggestions for handling them.",
            "category": "quality"
        },
        "trend_analysis": {
            "name": "Trend Analysis",
            "description": "Analyze trends and patterns over time",
            "prompt": "Analyze trends in this time-series data. Identify seasonal patterns, growth trends, and make predictions about future values.",
            "category": "forecasting"
        },
        "correlation_analysis": {
            "name": "Correlation Analysis",
            "description": "Find relationships between variables",
            "prompt": "Analyze correlations between variables in this dataset. Identify strong relationships and their business implications.",
            "category": "relationships"
        },
        "data_profiling": {
            "name": "Data Profiling",
            "description": "Complete profile of data quality and structure",
            "prompt": "Create a comprehensive data profile including data types, missing values, distributions, and quality issues.",
            "category": "quality"
        },
        "segmentation": {
            "name": "Customer Segmentation",
            "description": "Segment data into meaningful groups",
            "prompt": "Perform clustering or segmentation analysis on this dataset. Identify distinct groups and their characteristics.",
            "category": "clustering"
        },
        "performance_metrics": {
            "name": "Performance Metrics",
            "description": "Calculate key performance indicators",
            "prompt": "Calculate relevant KPIs and performance metrics from this dataset. Provide benchmarking and performance insights.",
            "category": "metrics"
        },
        "data_comparison": {
            "name": "Data Comparison",
            "description": "Compare datasets or time periods",
            "prompt": "Compare different segments or time periods in this data. Identify significant differences and their implications.",
            "category": "comparison"
        }
    }
    
    return {
        "templates": templates,
        "categories": list(set(t["category"] for t in templates.values()))
    }


@router.get("/insight-types")
async def get_insight_types() -> Dict:
    """Get available insight types for automated analysis."""
    insight_types = {
        "general": {
            "name": "General Analysis",
            "description": "Comprehensive overview of the dataset including statistics and patterns"
        },
        "anomalies": {
            "name": "Anomaly Detection",
            "description": "Identify outliers, unusual patterns, and data quality issues"
        },
        "trends": {
            "name": "Trend Analysis",
            "description": "Analyze time-based patterns, seasonality, and trends"
        },
        "patterns": {
            "name": "Pattern Discovery",
            "description": "Find relationships, correlations, and business patterns in the data"
        }
    }
    
    return {"insight_types": insight_types}


@router.post("/validate-prompt")
async def validate_workflow_prompt(prompt: str) -> Dict:
    """Validate and suggest improvements for workflow prompts."""
    try:
        # Basic validation rules
        validation_results = {
            "is_valid": True,
            "suggestions": [],
            "warnings": [],
            "score": 100
        }
        
        # Check prompt length
        if len(prompt.strip()) < 10:
            validation_results["is_valid"] = False
            validation_results["warnings"].append("Prompt is too short. Provide more detailed instructions.")
            validation_results["score"] -= 30
        
        # Check for specific data analysis keywords
        analysis_keywords = ["analyze", "calculate", "identify", "compare", "find", "detect", "summarize"]
        if not any(keyword in prompt.lower() for keyword in analysis_keywords):
            validation_results["suggestions"].append("Consider adding specific action words like 'analyze', 'calculate', or 'identify'.")
            validation_results["score"] -= 10
        
        # Check for data-specific terms
        data_terms = ["data", "dataset", "columns", "rows", "values", "statistics"]
        if not any(term in prompt.lower() for term in data_terms):
            validation_results["suggestions"].append("Include specific references to data elements you want to analyze.")
            validation_results["score"] -= 10
        
        # Check for question format
        if "?" in prompt:
            validation_results["suggestions"].append("Consider rephrasing questions as specific instructions for better results.")
        
        # Provide enhancement suggestions
        if validation_results["score"] > 80:
            validation_results["suggestions"].append("Your prompt looks good! Consider adding specific output format requirements if needed.")
        
        return validation_results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate prompt: {str(e)}")


@router.get("/repl/health")
async def check_repl_health(
    service: LangchainDataWorkflowService = Depends(get_workflow_service)
) -> Dict:
    """Check the health of the Docker Python REPL service."""
    try:
        is_healthy = await service.python_repl_tool.check_service_health()
        
        if is_healthy:
            capabilities = await service.python_repl_tool.get_service_capabilities()
            active_executions = await service.python_repl_tool.get_active_executions()
            
            return {
                "status": "healthy",
                "repl_service_url": service.repl_service_url,
                "capabilities": capabilities,
                "active_executions": active_executions
            }
        else:
            return {
                "status": "unhealthy",
                "repl_service_url": service.repl_service_url,
                "error": "REPL service is not responding"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "repl_service_url": service.repl_service_url,
            "error": str(e)
        }


@router.get("/repl/capabilities")
async def get_repl_capabilities(
    service: LangchainDataWorkflowService = Depends(get_workflow_service)
) -> Dict:
    """Get the capabilities of the Docker Python REPL service."""
    try:
        capabilities = await service.python_repl_tool.get_service_capabilities()
        return capabilities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get REPL capabilities: {str(e)}")


@router.get("/repl/active-executions")
async def get_repl_active_executions(
    service: LangchainDataWorkflowService = Depends(get_workflow_service)
) -> Dict:
    """Get currently active executions in the REPL service."""
    try:
        executions = await service.python_repl_tool.get_active_executions()
        return executions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active executions: {str(e)}")


class DirectREPLRequest(BaseModel):
    """Request model for direct REPL execution."""
    code: str
    variables: Optional[Dict[str, Any]] = None
    timeout_seconds: Optional[int] = 30


@router.post("/repl/execute")
async def execute_direct_repl(
    request: DirectREPLRequest,
    service: LangchainDataWorkflowService = Depends(get_workflow_service)
) -> Dict:
    """Execute Python code directly in the Docker REPL (for testing/debugging)."""
    try:
        result = await service.python_repl_tool._arun(
            code=request.code,
            variables=request.variables,
            timeout_seconds=request.timeout_seconds
        )
        
        return {
            "success": True,
            "result": result,
            "execution_method": "direct_repl"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "execution_method": "direct_repl"
        }


@router.get("/status")
async def get_workflow_service_status() -> Dict:
    """Get the status of workflow services."""
    return {
        "service_status": "active",
        "langchain_available": True,
        "docker_repl_available": True,
        "supported_data_sources": ["API", "MCP_SERVER", "WEB_SCRAPING"],
        "supported_workflows": ["data_analysis", "sql_queries", "data_pipelines", "auto_insights", "docker_repl"],
        "features": {
            "pandas_agent": True,
            "sql_agent": True,
            "docker_python_repl": True,
            "multi_source_pipelines": True,
            "automated_insights": True,
            "workflow_templates": True,
            "secure_execution": True
        }
    }