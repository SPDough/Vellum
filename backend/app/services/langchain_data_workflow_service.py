import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from langchain.agents import AgentExecutor, create_pandas_dataframe_agent, initialize_agent
from langchain.agents.agent_types import AgentType
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.sql_database import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine

from app.tools.docker_python_repl import create_docker_python_repl_tool

from app.models.data_source import (
    DataSourceConfiguration,
    DataSourceType,
    ProcessingConfig,
)
from app.services.base import BaseService
from app.services.data_source_service import DataSourceService

logger = logging.getLogger(__name__)


class LangchainDataWorkflowService(BaseService):
    """Service for executing data workflows using Langchain."""
    
    # Implement abstract methods from BaseService
    async def create(self, data: Any, context: Optional[Any] = None) -> Any:
        """Create method required by BaseService"""
        raise NotImplementedError("Create not implemented for LangchainDataWorkflowService")
    
    async def get_by_id(self, entity_id: str, context: Optional[Any] = None) -> Any:
        """Get by ID method required by BaseService"""
        raise NotImplementedError("Get by ID not implemented for LangchainDataWorkflowService")
    
    async def update(self, entity_id: str, data: Any, context: Optional[Any] = None) -> Any:
        """Update method required by BaseService"""
        raise NotImplementedError("Update not implemented for LangchainDataWorkflowService")
    
    async def delete(self, entity_id: str, context: Optional[Any] = None) -> Any:
        """Delete method required by BaseService"""
        raise NotImplementedError("Delete not implemented for LangchainDataWorkflowService")
    """Service for executing data workflows using Langchain."""
    
    def __init__(self, data_source_service: DataSourceService, openai_api_key: str, repl_service_url: str = "http://localhost:8001"):
        self.data_source_service = data_source_service
        self.repl_service_url = repl_service_url
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4",
            temperature=0
        )
        # Initialize Docker Python REPL tool
        self.python_repl_tool = create_docker_python_repl_tool(repl_service_url)
    
    async def execute_data_workflow(
        self, 
        config: DataSourceConfiguration,
        workflow_prompt: str,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a data workflow using Langchain agents.
        
        Args:
            config: Data source configuration
            workflow_prompt: Natural language description of what to do with the data
            custom_instructions: Additional instructions for data processing
            
        Returns:
            Dictionary containing results, processed data, and execution metadata
        """
        try:
            start_time = datetime.utcnow()
            
            # Pull data from source
            logger.info(f"Pulling data from {config.data_source_type} source: {config.name}")
            raw_data = await self.data_source_service._pull_data(
                DataSourceType(config.data_source_type),
                config.source_config
            )
            
            if not raw_data:
                raise ValueError("No data retrieved from source")
            
            # Convert to DataFrame if needed
            if isinstance(raw_data, list):
                df = pd.DataFrame(raw_data)
            else:
                df = raw_data.copy()
            
            logger.info(f"Retrieved {len(df)} records with {len(df.columns)} columns")
            
            # Apply basic processing if configured
            if config.processing_config:
                df = await self.data_source_service._process_data(df, config.processing_config)
                logger.info(f"After processing: {len(df)} records")
            
            # Execute Langchain workflow
            workflow_results = await self._execute_langchain_workflow(
                df, workflow_prompt, custom_instructions
            )
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "success": True,
                "execution_time_seconds": execution_time,
                "input_records": len(raw_data) if isinstance(raw_data, list) else len(raw_data),
                "processed_records": len(df),
                "workflow_results": workflow_results,
                "data_schema": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "sample_data": df.head(10).to_dict('records') if not df.empty else [],
            }
            
        except Exception as e:
            logger.error(f"Error executing data workflow: {str(e)}")
            return {
                "success": False,
                "error_message": str(e),
                "execution_time_seconds": (datetime.utcnow() - start_time).total_seconds(),
            }
    
    async def execute_data_workflow_with_docker_repl(
        self, 
        config: DataSourceConfiguration,
        workflow_prompt: str,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a data workflow using Docker Python REPL for secure code execution.
        This method provides enhanced security by running Python code in isolated containers.
        """
        try:
            start_time = datetime.utcnow()
            
            # Check REPL service health
            if not await self.python_repl_tool.check_service_health():
                raise ValueError("Docker Python REPL service is not available")
            
            # Pull data from source
            logger.info(f"Pulling data from {config.data_source_type} source: {config.name}")
            raw_data = await self.data_source_service._pull_data(
                DataSourceType(config.data_source_type),
                config.source_config
            )
            
            if not raw_data:
                raise ValueError("No data retrieved from source")
            
            # Convert to DataFrame if needed
            if isinstance(raw_data, list):
                df = pd.DataFrame(raw_data)
            else:
                df = raw_data.copy()
            
            logger.info(f"Retrieved {len(df)} records with {len(df.columns)} columns")
            
            # Apply basic processing if configured
            if config.processing_config:
                df = await self.data_source_service._process_data(df, config.processing_config)
                logger.info(f"After processing: {len(df)} records")
            
            # Execute workflow using Docker REPL agent
            workflow_results = await self._execute_docker_repl_workflow(
                df, workflow_prompt, custom_instructions
            )
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "success": True,
                "execution_time_seconds": execution_time,
                "input_records": len(raw_data) if isinstance(raw_data, list) else len(raw_data),
                "processed_records": len(df),
                "workflow_results": workflow_results,
                "data_schema": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "sample_data": df.head(10).to_dict('records') if not df.empty else [],
                "execution_method": "docker_repl"
            }
            
        except Exception as e:
            logger.error(f"Error executing Docker REPL workflow: {str(e)}")
            return {
                "success": False,
                "error_message": str(e),
                "execution_time_seconds": (datetime.utcnow() - start_time).total_seconds(),
                "execution_method": "docker_repl"
            }
    
    async def _execute_docker_repl_workflow(
        self, 
        df: pd.DataFrame, 
        workflow_prompt: str,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute workflow using Docker Python REPL agent."""
        
        # Create agent with Docker Python REPL tool
        tools = [self.python_repl_tool]
        
        agent = initialize_agent(
            tools=tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            return_intermediate_steps=True,
            max_iterations=10,
            max_execution_time=300  # 5 minutes max
        )
        
        # Convert DataFrame to JSON for injection into REPL
        df_json = df.to_json(orient='records')
        df_info = {
            'columns': list(df.columns),
            'shape': df.shape,
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
        
        # Build comprehensive prompt
        system_prompt = f"""You are a data analysis expert with access to a secure Python REPL environment.
        
        You have access to the following data:
        - Dataset shape: {df.shape[0]} rows, {df.shape[1]} columns
        - Columns: {', '.join(df.columns)}
        - Data types: {df_info['dtypes']}
        
        The data is available as JSON that you can load into a pandas DataFrame.
        
        Guidelines for your analysis:
        1. Start by loading the data into a pandas DataFrame
        2. Explore the data structure and basic statistics
        3. Perform the requested analysis using appropriate Python libraries
        4. Provide clear, actionable insights
        5. Format your final results clearly
        6. Use visualizations when helpful (matplotlib, seaborn)
        
        Available libraries: pandas, numpy, matplotlib, seaborn, scipy, scikit-learn, 
        sympy, statsmodels, and standard Python libraries.
        
        IMPORTANT: To load the data, use this code:
        ```python
        import pandas as pd
        import json
        
        # Load the data
        data_json = {df_json}
        df = pd.DataFrame(data_json)
        
        # Display basic info
        print("Data loaded successfully!")
        print(f"Shape: {{df.shape}}")
        print(f"Columns: {{list(df.columns)}}")
        print(df.head())
        ```
        """
        
        if custom_instructions:
            system_prompt += f"\n\nAdditional instructions: {custom_instructions}"
        
        full_prompt = f"{system_prompt}\n\nUser request: {workflow_prompt}\n\nPlease start by loading the data and then proceed with the analysis."
        
        try:
            # Execute the agent
            result = await asyncio.to_thread(
                agent.invoke,
                {"input": full_prompt}
            )
            
            return {
                "agent_response": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "execution_successful": True,
                "tool_used": "docker_python_repl"
            }
            
        except Exception as e:
            logger.error(f"Error in Docker REPL execution: {str(e)}")
            return {
                "agent_response": f"Error during analysis: {str(e)}",
                "intermediate_steps": [],
                "execution_successful": False,
                "error": str(e),
                "tool_used": "docker_python_repl"
            }
    
    async def _execute_langchain_workflow(
        self, 
        df: pd.DataFrame, 
        workflow_prompt: str,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute the main Langchain workflow on the data."""
        
        # Create pandas dataframe agent
        agent = create_pandas_dataframe_agent(
            self.llm,
            df,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
            allow_dangerous_code=True,  # Enable for data analysis
            return_intermediate_steps=True
        )
        
        # Build the prompt
        system_prompt = """You are a data analysis expert. You have access to a pandas DataFrame with data.
        Your task is to analyze the data according to the user's request and provide insights.
        
        Guidelines:
        1. Start by exploring the data structure and basic statistics
        2. Perform the requested analysis
        3. Provide clear, actionable insights
        4. If applicable, suggest data quality improvements
        5. Format your response as structured JSON when possible
        
        Available operations:
        - Data exploration (df.info(), df.describe(), df.head())
        - Filtering and grouping
        - Statistical analysis
        - Data visualization preparation
        - Data quality checks
        """
        
        if custom_instructions:
            system_prompt += f"\n\nAdditional instructions: {custom_instructions}"
        
        full_prompt = f"{system_prompt}\n\nUser request: {workflow_prompt}"
        
        try:
            # Execute the agent
            result = await asyncio.to_thread(
                agent.invoke,
                {"input": full_prompt}
            )
            
            return {
                "agent_response": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "execution_successful": True
            }
            
        except Exception as e:
            logger.error(f"Error in Langchain execution: {str(e)}")
            return {
                "agent_response": f"Error during analysis: {str(e)}",
                "intermediate_steps": [],
                "execution_successful": False,
                "error": str(e)
            }
    
    async def create_sql_workflow(
        self, 
        connection_string: str,
        query_prompt: str,
        table_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a workflow that uses SQL database agent.
        
        Args:
            connection_string: Database connection string
            query_prompt: Natural language description of the SQL query needed
            table_names: Optional list of specific tables to focus on
            
        Returns:
            Dictionary containing query results and metadata
        """
        try:
            start_time = datetime.utcnow()
            
            # Create SQL database connection
            engine = create_engine(connection_string)
            db = SQLDatabase(engine)
            
            # Create SQL agent
            sql_agent = create_sql_agent(
                llm=self.llm,
                db=db,
                agent_type=AgentType.OPENAI_FUNCTIONS,
                verbose=True,
                return_intermediate_steps=True
            )
            
            # Build the prompt
            system_prompt = """You are a SQL expert. You have access to a database and need to write queries to answer the user's question.
            
            Guidelines:
            1. First, explore the database schema to understand the available tables and columns
            2. Write efficient SQL queries to answer the user's question
            3. Provide clear explanations of your queries
            4. If the query returns data, summarize the key findings
            5. Suggest optimizations if applicable
            """
            
            if table_names:
                system_prompt += f"\n\nFocus on these tables: {', '.join(table_names)}"
            
            full_prompt = f"{system_prompt}\n\nUser question: {query_prompt}"
            
            # Execute the agent
            result = await asyncio.to_thread(
                sql_agent.invoke,
                {"input": full_prompt}
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "success": True,
                "execution_time_seconds": execution_time,
                "agent_response": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "sql_queries_executed": self._extract_sql_queries(result.get("intermediate_steps", [])),
            }
            
        except Exception as e:
            logger.error(f"Error executing SQL workflow: {str(e)}")
            return {
                "success": False,
                "error_message": str(e),
                "execution_time_seconds": (datetime.utcnow() - start_time).total_seconds(),
            }
    
    def _extract_sql_queries(self, intermediate_steps: List) -> List[str]:
        """Extract SQL queries from intermediate steps."""
        queries = []
        for step in intermediate_steps:
            if isinstance(step, tuple) and len(step) >= 2:
                action = step[0]
                if hasattr(action, 'tool') and 'sql' in action.tool.lower():
                    if hasattr(action, 'tool_input'):
                        queries.append(action.tool_input)
        return queries
    
    async def create_data_pipeline_workflow(
        self,
        source_configs: List[DataSourceConfiguration],
        pipeline_instructions: str,
        output_format: str = "dataframe"
    ) -> Dict[str, Any]:
        """
        Create a workflow that processes data from multiple sources.
        
        Args:
            source_configs: List of data source configurations
            pipeline_instructions: Instructions for processing and combining data
            output_format: Format for output ("dataframe", "json", "csv")
            
        Returns:
            Dictionary containing pipeline results
        """
        try:
            start_time = datetime.utcnow()
            datasets = {}
            
            # Pull data from all sources
            for i, config in enumerate(source_configs):
                logger.info(f"Processing source {i+1}/{len(source_configs)}: {config.name}")
                
                data = await self.data_source_service._pull_data(
                    DataSourceType(config.data_source_type),
                    config.source_config
                )
                
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = data.copy() if data is not None and hasattr(data, 'copy') else data
                
                # Apply processing if configured
                if config.processing_config:
                    df = await self.data_source_service._process_data(df, config.processing_config)
                
                datasets[f"dataset_{i+1}_{config.name.replace(' ', '_')}"] = df
            
            # Create a combined workflow prompt
            dataset_info = "\n".join([
                f"- {name}: {len(df)} records, columns: {list(df.columns)}"
                for name, df in datasets.items()
            ])
            
            workflow_prompt = f"""
            You have access to the following datasets:
            {dataset_info}
            
            Pipeline instructions: {pipeline_instructions}
            
            Your task is to:
            1. Analyze each dataset
            2. Process and combine the data as instructed
            3. Provide insights and results
            4. Suggest data quality improvements if needed
            """
            
            # For now, work with the largest dataset as primary
            # In a more advanced version, you could create a custom agent
            # that has access to all datasets
            primary_dataset = max(datasets.values(), key=len)
            
            workflow_results = await self._execute_langchain_workflow(
                primary_dataset, workflow_prompt
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "success": True,
                "execution_time_seconds": execution_time,
                "sources_processed": len(source_configs),
                "total_records": sum(len(df) for df in datasets.values()),
                "workflow_results": workflow_results,
                "dataset_summaries": {
                    name: {
                        "records": len(df),
                        "columns": list(df.columns),
                        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
                    }
                    for name, df in datasets.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing data pipeline workflow: {str(e)}")
            return {
                "success": False,
                "error_message": str(e),
                "execution_time_seconds": (datetime.utcnow() - start_time).total_seconds(),
            }
    
    async def create_automated_insights_workflow(
        self, 
        config: DataSourceConfiguration,
        insight_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Create an automated workflow that generates insights from data.
        
        Args:
            config: Data source configuration
            insight_type: Type of insights to generate ("general", "anomalies", "trends", "patterns")
            
        Returns:
            Dictionary containing automated insights
        """
        insight_prompts = {
            "general": """
            Perform a comprehensive analysis of this dataset:
            1. Data overview and quality assessment
            2. Statistical summary of numeric columns
            3. Distribution analysis
            4. Key patterns and relationships
            5. Notable observations and recommendations
            """,
            "anomalies": """
            Focus on detecting anomalies and outliers in this dataset:
            1. Identify statistical outliers in numeric columns
            2. Find unusual patterns or values
            3. Detect missing data patterns
            4. Highlight data quality issues
            5. Suggest data cleaning steps
            """,
            "trends": """
            Analyze trends and time-based patterns in this dataset:
            1. Identify time-based columns
            2. Analyze trends over time
            3. Detect seasonality or cyclical patterns
            4. Compare different time periods
            5. Forecast insights if applicable
            """,
            "patterns": """
            Discover patterns and relationships in this dataset:
            1. Correlation analysis between variables
            2. Grouping and segmentation opportunities
            3. Feature importance analysis
            4. Cluster identification
            5. Business rule discovery
            """
        }
        
        prompt = insight_prompts.get(insight_type, insight_prompts["general"])
        
        return await self.execute_data_workflow(
            config, 
            prompt,
            f"Focus on {insight_type} insights. Provide actionable recommendations."
        )
