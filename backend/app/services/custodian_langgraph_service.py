"""
Custodian Data Analysis LangGraph Service

This service provides LangGraph workflows for analyzing custodian data,
including data extraction, processing, and natural language querying.
"""

import asyncio
import logging
import pandas as pd
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import httpx
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.models.data_source import DataSourceType
from app.services.custodian_apis import get_custodian_api_spec
from app.services.data_source_service import DataSourceService

logger = logging.getLogger(__name__)


class CustodianDataState(BaseModel):
    """State model for custodian data analysis workflows."""
    
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    data: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    dataframe: Optional[pd.DataFrame] = None
    analysis_results: Dict[str, Any] = Field(default_factory=dict)


class CustodianAPIConfig(BaseModel):
    """Configuration for custodian API connections."""
    
    base_url: str
    api_key: Optional[str] = None
    auth_type: str = "bearer"  # bearer, api_key, oauth
    headers: Dict[str, str] = Field(default_factory=dict)
    timeout: int = 30


class DataExtractionNode:
    """LangGraph node for extracting data from custodian APIs."""
    
    def __init__(self, api_config: CustodianAPIConfig):
        self.api_config = api_config
        self.node_id = str(uuid4())
        self.node_type = "DATA_EXTRACTION"
        self.name = "Custodian Data Extraction"
    
    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from custodian API."""
        try:
            logger.info(f"Executing data extraction node: {self.node_id}")
            
            # Extract parameters from state
            endpoint = state.get("context", {}).get("endpoint", "/positions")
            params = state.get("context", {}).get("params", {})
            
            # Make API request
            async with httpx.AsyncClient() as client:
                headers = self.api_config.headers.copy()
                
                if self.api_config.auth_type == "bearer" and self.api_config.api_key:
                    headers["Authorization"] = f"Bearer {self.api_config.api_key}"
                elif self.api_config.auth_type == "api_key" and self.api_config.api_key:
                    headers["X-API-Key"] = self.api_config.api_key
                
                response = await client.get(
                    f"{self.api_config.base_url}{endpoint}",
                    headers=headers,
                    params=params,
                    timeout=self.api_config.timeout
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Convert to DataFrame
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict) and "data" in data:
                    df = pd.DataFrame(data["data"])
                elif isinstance(data, dict):
                    df = pd.DataFrame([data])
                else:
                    df = pd.DataFrame()
                
                # Update state
                new_state = {
                    **state,
                    "dataframe": df,
                    "data": {
                        **state.get("data", {}),
                        "raw_data": data,
                        "record_count": len(df),
                        "columns": df.columns.tolist() if not df.empty else [],
                        "extracted_at": datetime.utcnow().isoformat()
                    },
                    "messages": state.get("messages", []) + [
                        {
                            "role": "system",
                            "content": f"Successfully extracted {len(df)} records from custodian API",
                            "timestamp": datetime.utcnow().isoformat(),
                            "node_id": self.node_id
                        }
                    ]
                }
                
                logger.info(f"Data extraction completed: {len(df)} records")
                return new_state
                
        except Exception as e:
            logger.error(f"Data extraction failed: {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [f"Data extraction failed: {str(e)}"],
                "messages": state.get("messages", []) + [
                    {
                        "role": "system",
                        "content": f"Data extraction failed: {str(e)}",
                        "timestamp": datetime.utcnow().isoformat(),
                        "node_id": self.node_id
                    }
                ]
            }


class DataAnalysisNode:
    """LangGraph node for analyzing custodian data using LLM."""
    
    def __init__(self):
        self.node_id = str(uuid4())
        self.node_type = "DATA_ANALYSIS"
        self.name = "Custodian Data Analysis"
        
        settings = get_settings()
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model="gpt-4",
            temperature=0.1
        )
    
    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data using LLM."""
        try:
            logger.info(f"Executing data analysis node: {self.node_id}")
            
            df = state.get("dataframe")
            if df is None or df.empty:
                return {
                    **state,
                    "errors": state.get("errors", []) + ["No data available for analysis"],
                    "messages": state.get("messages", []) + [
                        {
                            "role": "system",
                            "content": "No data available for analysis",
                            "timestamp": datetime.utcnow().isoformat(),
                            "node_id": self.node_id
                        }
                    ]
                }
            
            # Get user question from context
            user_question = state.get("context", {}).get("user_question", "Analyze this data")
            
            # Prepare data summary for LLM
            data_summary = f"""
            Data Summary:
            - Shape: {df.shape}
            - Columns: {df.columns.tolist()}
            - Data Types: {df.dtypes.to_dict()}
            - Sample Data:
            {df.head().to_string()}
            - Basic Statistics:
            {df.describe().to_string() if df.select_dtypes(include=['number']).shape[1] > 0 else 'No numeric columns'}
            """
            
            # Create messages for LLM
            messages = [
                SystemMessage(content="""You are a financial data analyst specializing in custodian data analysis. 
                Analyze the provided data and answer questions about it. Provide insights, trends, and actionable information.
                When analyzing financial data, consider:
                - Position values and changes
                - Risk metrics
                - Performance indicators
                - Compliance implications
                - Market trends
                
                Format your response in a clear, structured manner with key insights highlighted."""),
                HumanMessage(content=f"Data to analyze:\n{data_summary}\n\nUser question: {user_question}")
            ]
            
            # Get LLM response
            response = await self.llm.ainvoke(messages)
            
            # Update state
            new_state = {
                **state,
                "analysis_results": {
                    **state.get("analysis_results", {}),
                    "question": user_question,
                    "answer": response.content,
                    "analysis_timestamp": datetime.utcnow().isoformat()
                },
                "messages": state.get("messages", []) + [
                    {
                        "role": "assistant",
                        "content": response.content,
                        "timestamp": datetime.utcnow().isoformat(),
                        "node_id": self.node_id
                    }
                ]
            }
            
            logger.info("Data analysis completed successfully")
            return new_state
            
        except Exception as e:
            logger.error(f"Data analysis failed: {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [f"Data analysis failed: {str(e)}"],
                "messages": state.get("messages", []) + [
                    {
                        "role": "system",
                        "content": f"Data analysis failed: {str(e)}",
                        "timestamp": datetime.utcnow().isoformat(),
                        "node_id": self.node_id
                    }
                ]
            }


class CustodianLangGraphService:
    """Service for managing custodian data analysis LangGraph workflows."""
    
    def __init__(self):
        self.graphs: Dict[str, StateGraph] = {}
        self.workflow_custodian: Dict[str, str] = {}
        self.api_configs: Dict[str, CustodianAPIConfig] = {}
        self._register_default_configs()
    
    def _register_default_configs(self):
        """Register default custodian API configurations."""
        state_street_spec = get_custodian_api_spec("state_street")
        if state_street_spec:
            self.api_configs["state_street"] = CustodianAPIConfig(
                base_url=state_street_spec.base_url,
                auth_type=state_street_spec.auth_type,
            )
        else:
            self.api_configs["state_street"] = CustodianAPIConfig(
                base_url="https://api.statestreet.com/v1",
                auth_type="bearer",
            )
        self.api_configs["bny_mellon"] = CustodianAPIConfig(
            base_url="https://api.bnymellon.com/v1",
            auth_type="bearer",
        )
        self.api_configs["jpmorgan"] = CustodianAPIConfig(
            base_url="https://api.jpmorgan.com/v1",
            auth_type="bearer",
        )
        logger.info("Registered default custodian API configurations")
    
    async def create_custodian_analysis_workflow(
        self, 
        custodian_name: str,
        api_key: Optional[str] = None
    ) -> str:
        """Create a custodian data analysis workflow."""
        try:
            workflow_id = str(uuid4())
            
            # Get or create API config
            if custodian_name not in self.api_configs:
                self.api_configs[custodian_name] = CustodianAPIConfig(
                    base_url=f"https://api.{custodian_name.lower().replace(' ', '')}.com/v1",
                    auth_type="bearer"
                )
            
            api_config = self.api_configs[custodian_name]
            if api_key:
                api_config.api_key = api_key
            
            # Create workflow nodes
            extraction_node = DataExtractionNode(api_config)
            analysis_node = DataAnalysisNode()
            
            # Create state graph
            workflow = StateGraph(CustodianDataState)
            
            # Add nodes
            workflow.add_node("extract_data", extraction_node)
            workflow.add_node("analyze_data", analysis_node)
            
            # Define workflow flow
            workflow.set_entry_point("extract_data")
            workflow.add_edge("extract_data", "analyze_data")
            workflow.add_edge("analyze_data", END)
            
            # Compile workflow
            compiled_graph = workflow.compile()
            self.graphs[workflow_id] = compiled_graph
            self.workflow_custodian[workflow_id] = custodian_name
            
            logger.info(f"Created custodian analysis workflow: {workflow_id}")
            return workflow_id
            
        except Exception as e:
            logger.error(f"Failed to create custodian analysis workflow: {e}")
            raise
    
    async def execute_custodian_analysis(
        self,
        workflow_id: str,
        endpoint: str = "/positions",
        capability_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        user_question: str = "Analyze this custodian data",
    ) -> Dict[str, Any]:
        """Execute a custodian data analysis workflow. If capability_id is set and workflow has a spec-backed custodian, endpoint is resolved from the spec."""
        try:
            if workflow_id not in self.graphs:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            graph = self.graphs[workflow_id]
            resolved_endpoint = endpoint
            if capability_id:
                custodian_name = self.workflow_custodian.get(workflow_id)
                spec = get_custodian_api_spec(custodian_name) if custodian_name else None
                if spec:
                    cap = spec.get_capability(capability_id)
                    if cap:
                        resolved_endpoint = cap.path
                    else:
                        raise ValueError(
                            f"Unknown capability {capability_id} for {custodian_name}. "
                            f"Available: {[c.id for c in spec.capabilities]}"
                        )
            
            # Prepare initial state
            initial_state = CustodianDataState(
                context={
                    "endpoint": resolved_endpoint,
                    "params": params or {},
                    "user_question": user_question,
                    "workflow_id": workflow_id,
                    "execution_id": str(uuid4()),
                    "start_time": datetime.utcnow().isoformat(),
                }
            )
            
            logger.info(f"Executing custodian analysis workflow: {workflow_id}")
            
            # Execute workflow
            result = await graph.ainvoke(initial_state.model_dump())
            
            # Convert result to dict
            result_dict = result.model_dump() if hasattr(result, "model_dump") else dict(result)
            result_dict["context"]["end_time"] = datetime.utcnow().isoformat()
            result_dict["context"]["status"] = (
                "COMPLETED" if not result_dict.get("errors") else "FAILED"
            )
            
            # Convert DataFrame to serializable format
            if result_dict.get("dataframe") is not None:
                df = result_dict["dataframe"]
                result_dict["data"]["dataframe_summary"] = {
                    "shape": df.shape,
                    "columns": df.columns.tolist(),
                    "dtypes": df.dtypes.astype(str).to_dict(),
                    "sample_data": df.head(10).to_dict('records'),
                    "null_counts": df.isnull().sum().to_dict()
                }
                # Remove the actual DataFrame from response
                del result_dict["dataframe"]
            
            logger.info(f"Custodian analysis workflow completed: {workflow_id}")
            return result_dict
            
        except Exception as e:
            logger.error(f"Failed to execute custodian analysis workflow: {e}")
            raise
    
    def list_available_custodians(self) -> List[Dict[str, Any]]:
        """List available custodian configurations with capabilities when defined."""
        result = []
        for name, config in self.api_configs.items():
            entry = {
                "name": name,
                "base_url": config.base_url,
                "auth_type": config.auth_type,
                "configured": config.api_key is not None,
            }
            spec = get_custodian_api_spec(name)
            if spec:
                entry["display_name"] = spec.display_name
                entry["capabilities"] = spec.to_capabilities_list()
                if spec.version:
                    entry["version"] = spec.version
                if getattr(spec, "source_document", None):
                    entry["source_document"] = spec.source_document
            result.append(entry)
        return result
    
    def add_custodian_config(
        self,
        name: str,
        base_url: str,
        auth_type: str = "bearer",
        api_key: Optional[str] = None
    ) -> None:
        """Add a new custodian configuration."""
        self.api_configs[name] = CustodianAPIConfig(
            base_url=base_url,
            auth_type=auth_type,
            api_key=api_key
        )
        logger.info(f"Added custodian configuration: {name}")


# Service instance
_custodian_langgraph_service: Optional[CustodianLangGraphService] = None


def get_custodian_langgraph_service() -> CustodianLangGraphService:
    """Get custodian LangGraph service instance."""
    global _custodian_langgraph_service
    if _custodian_langgraph_service is None:
        _custodian_langgraph_service = CustodianLangGraphService()
    return _custodian_langgraph_service
