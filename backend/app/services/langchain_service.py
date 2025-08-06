import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain.schema.runnable import Runnable, RunnableSequence
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.core.config import get_settings
from app.services.fibo_service import get_fibo_service
from app.services.neo4j_service import get_neo4j_service

logger = logging.getLogger(__name__)


class LangchainWorkflowState(BaseModel):
    """State model for Langchain workflows."""

    messages: List[Dict[str, Any]] = []
    data: Dict[str, Any] = {}
    context: Dict[str, Any] = {}
    errors: List[str] = []


class LangchainPositionAnalysisWorkflow:
    """Langchain workflow for position analysis using LLM."""

    def __init__(self, llm: Any = None):
        self.workflow_id = str(uuid4())
        self.name = "Position Analysis Workflow"
        self.description = "Analyzes banking positions using LLM with FIBO context"
        self.llm = llm
        self.chain = None
        self._setup_chain()

    def _setup_chain(self):
        """Setup the Langchain workflow chain."""
        try:
            if not self.llm:
                settings = get_settings()
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
                    logger.warning("No LLM API keys configured")
                    return

            # Create the analysis prompt
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a banking operations analyst specializing in position analysis.

Context: You are analyzing positions within a FIBO (Financial Industry Business Ontology) framework.
Your role is to:
1. Analyze position data for potential risks or anomalies
2. Provide insights on position concentrations
3. Identify potential compliance issues
4. Suggest optimization recommendations

Guidelines:
- Be concise and specific in your analysis
- Focus on actionable insights
- Consider risk management implications
- Reference FIBO standards where applicable""",
                    ),
                    (
                        "human",
                        """Please analyze the following position data:

Position Data:
{position_data}

FIBO Context:
{fibo_context}

Provide a structured analysis including:
1. Risk Assessment
2. Compliance Notes
3. Recommendations
4. Key Metrics Summary""",
                    ),
                ]
            )

            # Create the chain
            self.chain = prompt | self.llm
            logger.info(f"Langchain workflow chain setup completed: {self.workflow_id}")

        except Exception as e:
            logger.error(f"Failed to setup Langchain workflow: {e}")
            raise

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the position analysis workflow."""
        try:
            if not self.chain:
                raise ValueError("Workflow chain not properly initialized")

            logger.info(f"Executing Langchain workflow: {self.workflow_id}")

            position_data = input_data.get("positions", [])
            if not position_data:
                return {
                    "error": "No position data provided",
                    "workflow_id": self.workflow_id,
                    "status": "FAILED",
                }

            # Get FIBO context
            fibo_context = await self._get_fibo_context(position_data)

            # Prepare data for analysis
            formatted_positions = self._format_positions(position_data)

            # Execute the chain
            result = await asyncio.to_thread(
                self.chain.invoke,
                {"position_data": formatted_positions, "fibo_context": fibo_context},
            )

            analysis_result = {
                "workflow_id": self.workflow_id,
                "workflow_type": "LANGCHAIN",
                "status": "COMPLETED",
                "input_data": input_data,
                "analysis": {
                    "llm_response": (
                        result.content if hasattr(result, "content") else str(result)
                    ),
                    "model_used": getattr(self.llm, "model_name", "unknown"),
                    "fibo_context": fibo_context,
                    "position_count": len(position_data),
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                },
                "execution_time": datetime.utcnow().isoformat(),
                "metadata": {
                    "chain_type": "prompt_llm",
                    "workflow_name": self.name,
                    "workflow_description": self.description,
                },
            }

            logger.info(f"Langchain workflow completed: {self.workflow_id}")
            return analysis_result

        except Exception as e:
            logger.error(f"Langchain workflow execution failed: {e}")
            return {
                "workflow_id": self.workflow_id,
                "workflow_type": "LANGCHAIN",
                "status": "FAILED",
                "error": str(e),
                "execution_time": datetime.utcnow().isoformat(),
            }

    async def _get_fibo_context(
        self, position_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get FIBO ontology context for positions."""
        try:
            fibo_service = await get_fibo_service()
            neo4j_service = await get_neo4j_service()

            # Get FIBO mappings for position types
            fibo_mappings = []
            for position in position_data[:5]:  # Limit for performance
                position_id = position.get("id")
                if position_id:
                    fibo_mapping = await fibo_service.map_entity_to_fibo(
                        "Position", position_id, "FIBOPositionHolding"
                    )
                    if fibo_mapping:
                        fibo_mappings.append(fibo_mapping)

            return {
                "fibo_mappings_count": len(fibo_mappings),
                "sample_mappings": fibo_mappings[:3],
                "ontology_version": "FIBO 2023",
                "relevant_concepts": [
                    "PositionHolding",
                    "FinancialInstrument",
                    "Portfolio",
                    "RiskMeasure",
                ],
            }

        except Exception as e:
            logger.warning(f"Failed to get FIBO context: {e}")
            return {"error": str(e), "fibo_available": False}

    def _format_positions(self, positions: List[Dict[str, Any]]) -> str:
        """Format position data for LLM analysis."""
        formatted = []
        for i, pos in enumerate(positions[:10]):  # Limit for token efficiency
            formatted.append(
                f"""
Position {i+1}:
- ID: {pos.get('id', 'N/A')}
- Security: {pos.get('security_id', 'N/A')}
- Quantity: {pos.get('quantity', 0):,}
- Market Value: ${pos.get('market_value', 0):,.2f}
- Currency: {pos.get('currency', 'USD')}
- Type: {pos.get('position_type', 'LONG')}
- Account: {pos.get('account_id', 'N/A')}
"""
            )

        total_value = sum(pos.get("market_value", 0) for pos in positions)
        summary = (
            f"\nSummary: {len(positions)} positions, Total Value: ${total_value:,.2f}"
        )

        return "\n".join(formatted) + summary


class LangchainTradeValidationWorkflow:
    """Langchain workflow for trade validation using rule-based LLM analysis."""

    def __init__(self, llm: Any = None):
        self.workflow_id = str(uuid4())
        self.name = "Trade Validation Workflow"
        self.description = "Validates trade data using LLM-based rule analysis"
        self.llm = llm
        self.chain = None
        self._setup_chain()

    def _setup_chain(self):
        """Setup the trade validation chain."""
        try:
            if not self.llm:
                settings = get_settings()
                if settings.anthropic_api_key:
                    self.llm = ChatAnthropic(
                        model="claude-3-haiku-20240307",
                        api_key=settings.anthropic_api_key,
                        temperature=0,
                    )
                elif settings.openai_api_key:
                    self.llm = ChatOpenAI(
                        model="gpt-3.5-turbo",
                        api_key=settings.openai_api_key,
                        temperature=0,
                    )
                else:
                    logger.warning("No LLM API keys configured")
                    return

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a trade validation specialist for banking operations.

Your task is to validate trade data against standard banking rules and regulations:

VALIDATION RULES:
1. Trade Amount Limits: Flag trades over $10M for manual review
2. Settlement Date: Must be T+0 to T+3 for most instruments
3. Currency Validation: Ensure currency codes are valid ISO codes
4. Counterparty Check: Verify counterparty is on approved list
5. Market Hours: Trades should occur during market hours
6. Instrument Validation: Security ID must be valid format

Respond with structured validation results in JSON format.""",
                    ),
                    (
                        "human",
                        """Validate the following trade:

Trade Data:
{trade_data}

Validation Context:
{validation_context}

Provide validation results as JSON with:
- valid: boolean
- issues: array of validation issues
- risk_level: LOW/MEDIUM/HIGH
- recommendations: array of recommendations""",
                    ),
                ]
            )

            self.chain = prompt | self.llm
            logger.info(f"Trade validation chain setup completed: {self.workflow_id}")

        except Exception as e:
            logger.error(f"Failed to setup trade validation chain: {e}")
            raise

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trade validation workflow."""
        try:
            if not self.chain:
                raise ValueError("Validation chain not properly initialized")

            logger.info(f"Executing trade validation workflow: {self.workflow_id}")

            trade_data = input_data.get("trade", {})
            if not trade_data:
                return {
                    "error": "No trade data provided",
                    "workflow_id": self.workflow_id,
                    "status": "FAILED",
                }

            # Prepare validation context
            validation_context = {
                "current_time": datetime.utcnow().isoformat(),
                "max_trade_amount": 10000000,  # $10M
                "valid_currencies": ["USD", "EUR", "GBP", "JPY", "CAD"],
                "market_open": "09:30",
                "market_close": "16:00",
            }

            # Execute validation
            result = await asyncio.to_thread(
                self.chain.invoke,
                {
                    "trade_data": self._format_trade(trade_data),
                    "validation_context": validation_context,
                },
            )

            validation_result = {
                "workflow_id": self.workflow_id,
                "workflow_type": "LANGCHAIN",
                "status": "COMPLETED",
                "input_data": input_data,
                "validation": {
                    "llm_response": (
                        result.content if hasattr(result, "content") else str(result)
                    ),
                    "model_used": getattr(self.llm, "model_name", "unknown"),
                    "validation_timestamp": datetime.utcnow().isoformat(),
                    "context": validation_context,
                },
                "execution_time": datetime.utcnow().isoformat(),
                "metadata": {
                    "workflow_name": self.name,
                    "workflow_description": self.description,
                },
            }

            logger.info(f"Trade validation workflow completed: {self.workflow_id}")
            return validation_result

        except Exception as e:
            logger.error(f"Trade validation workflow failed: {e}")
            return {
                "workflow_id": self.workflow_id,
                "workflow_type": "LANGCHAIN",
                "status": "FAILED",
                "error": str(e),
                "execution_time": datetime.utcnow().isoformat(),
            }

    def _format_trade(self, trade: Dict[str, Any]) -> str:
        """Format trade data for validation."""
        return f"""
Trade ID: {trade.get('id', 'N/A')}
Security ID: {trade.get('security_id', 'N/A')}
Trade Type: {trade.get('trade_type', 'N/A')}
Quantity: {trade.get('quantity', 0):,}
Price: ${trade.get('price', 0):.2f}
Total Amount: ${trade.get('total_amount', 0):,.2f}
Currency: {trade.get('currency', 'USD')}
Settlement Date: {trade.get('settlement_date', 'N/A')}
Counterparty: {trade.get('counterparty', 'N/A')}
Trade Time: {trade.get('trade_time', 'N/A')}
"""


class LangchainService:
    """Service for managing Langchain workflows."""

    def __init__(self):
        self.workflows: Dict[str, Any] = {}
        self.workflow_templates = {
            "position_analysis": LangchainPositionAnalysisWorkflow,
            "trade_validation": LangchainTradeValidationWorkflow,
        }
        logger.info("Langchain service initialized")

    async def create_position_analysis_workflow(self) -> str:
        """Create a position analysis workflow."""
        try:
            workflow = LangchainPositionAnalysisWorkflow()
            workflow_id = workflow.workflow_id
            self.workflows[workflow_id] = workflow

            logger.info(f"Created position analysis workflow: {workflow_id}")
            return workflow_id

        except Exception as e:
            logger.error(f"Failed to create position analysis workflow: {e}")
            raise

    async def create_trade_validation_workflow(self) -> str:
        """Create a trade validation workflow."""
        try:
            workflow = LangchainTradeValidationWorkflow()
            workflow_id = workflow.workflow_id
            self.workflows[workflow_id] = workflow

            logger.info(f"Created trade validation workflow: {workflow_id}")
            return workflow_id

        except Exception as e:
            logger.error(f"Failed to create trade validation workflow: {e}")
            raise

    async def execute_workflow(
        self, workflow_id: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a Langchain workflow."""
        try:
            if workflow_id not in self.workflows:
                raise ValueError(f"Workflow {workflow_id} not found")

            workflow = self.workflows[workflow_id]
            result = await workflow.execute(input_data)

            logger.info(f"Executed Langchain workflow: {workflow_id}")
            return result

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "ERROR",
                "error": str(e),
                "execution_time": datetime.utcnow().isoformat(),
            }

    async def get_workflow_info(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a workflow."""
        if workflow_id not in self.workflows:
            return None

        workflow = self.workflows[workflow_id]
        return {
            "workflow_id": workflow_id,
            "name": getattr(workflow, "name", "Unknown"),
            "description": getattr(workflow, "description", ""),
            "status": "ACTIVE",
            "workflow_type": "LANGCHAIN",
            "created_at": datetime.utcnow().isoformat(),
        }

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all Langchain workflows."""
        return [
            {
                "workflow_id": workflow_id,
                "name": getattr(workflow, "name", "Unknown"),
                "description": getattr(workflow, "description", ""),
                "status": "ACTIVE",
                "workflow_type": "LANGCHAIN",
            }
            for workflow_id, workflow in self.workflows.items()
        ]

    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get available workflow templates."""
        return [
            {
                "template_id": template_id,
                "name": template_class.__name__,
                "description": getattr(
                    template_class, "__doc__", "No description available"
                ),
                "workflow_type": "LANGCHAIN",
            }
            for template_id, template_class in self.workflow_templates.items()
        ]


# Global service instance
langchain_service = LangchainService()


async def get_langchain_service() -> LangchainService:
    """Dependency injection for Langchain service."""
    return langchain_service
