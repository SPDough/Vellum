import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from langgraph.graph import Graph, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel

from app.models.workflow import NodeType
from app.services.fibo_service import get_fibo_service
from app.services.neo4j_service import get_neo4j_service

logger = logging.getLogger(__name__)


class LangGraphState(BaseModel):
    """State model for LangGraph workflows."""

    messages: List[Dict[str, Any]] = []
    data: Dict[str, Any] = {}
    context: Dict[str, Any] = {}
    errors: List[str] = []


class FIBOPositionMappingNode:
    """LangGraph node for mapping position data to FIBO ontology."""

    def __init__(self) -> None:
        self.node_id = str(uuid4())
        self.node_type = "FIBO_MAPPING"
        self.name = "FIBO Position Mapping Node"

    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the FIBO position mapping logic."""
        try:
            logger.info(f"Executing FIBO mapping node: {self.node_id}")

            position_data = state.get("data", {}).get("positions", [])
            if not position_data:
                logger.warning("No position data found in state")
                return {
                    **state,
                    "errors": state.get("errors", []) + ["No position data provided"],
                }

            fibo_service = await get_fibo_service()
            neo4j_service = await get_neo4j_service()

            mapped_positions = []
            mapping_results = []

            for position in position_data:
                try:
                    fibo_position = await self._map_position_to_fibo(
                        position, fibo_service, neo4j_service
                    )

                    if fibo_position:
                        mapped_positions.append(fibo_position)
                        mapping_results.append(
                            {
                                "original_id": position.get("id"),
                                "fibo_id": fibo_position.get("id"),
                                "status": "SUCCESS",
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                    else:
                        mapping_results.append(
                            {
                                "original_id": position.get("id"),
                                "status": "FAILED",
                                "error": "Failed to create FIBO mapping",
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )

                except Exception as e:
                    logger.error(f"Failed to map position {position.get('id')}: {e}")
                    mapping_results.append(
                        {
                            "original_id": position.get("id"),
                            "status": "ERROR",
                            "error": str(e),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

            new_state = {
                **state,
                "data": {
                    **state.get("data", {}),
                    "fibo_positions": mapped_positions,
                    "mapping_results": mapping_results,
                },
                "messages": state.get("messages", [])
                + [
                    {
                        "role": "system",
                        "content": f"Mapped {len(mapped_positions)} positions to FIBO ontology",
                        "timestamp": datetime.utcnow().isoformat(),
                        "node_id": self.node_id,
                    }
                ],
            }

            logger.info(
                f"FIBO mapping completed: {len(mapped_positions)} positions mapped"
            )
            return new_state

        except Exception as e:
            logger.error(f"FIBO mapping node failed: {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [f"FIBO mapping failed: {str(e)}"],
                "messages": state.get("messages", [])
                + [
                    {
                        "role": "system",
                        "content": f"FIBO mapping failed: {str(e)}",
                        "timestamp": datetime.utcnow().isoformat(),
                        "node_id": self.node_id,
                        "level": "ERROR",
                    }
                ],
            }

    async def _map_position_to_fibo(
        self, position: Dict[str, Any], fibo_service: Any, neo4j_service: Any
    ) -> Optional[Dict[str, Any]]:
        """Map a single position to FIBO ontology."""
        try:
            position_id = position.get("id", str(uuid4()))

            existing_position = await neo4j_service.get_entity("Position", position_id)

            if not existing_position:
                position_entity = {
                    "id": position_id,
                    "name": f"Position {position_id}",
                    "account_id": position.get("account_id"),
                    "security_id": position.get("security_id"),
                    "quantity": position.get("quantity", 0),
                    "market_value": position.get("market_value", 0),
                    "currency": position.get("currency", "USD"),
                    "valuation_date": position.get(
                        "valuation_date", datetime.utcnow().isoformat()
                    ),
                    "position_type": position.get("position_type", "LONG"),
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }

                await neo4j_service.create_entity("Position", position_entity)

            fibo_position = await fibo_service.map_entity_to_fibo(
                "Position", position_id, "FIBOPositionHolding"
            )

            if fibo_position is not None:
                return dict(fibo_position)
            return None

        except Exception as e:
            logger.error(f"Failed to map position to FIBO: {e}")
            return None


class TradeValidationNode:
    """LangGraph node for trade validation and compliance checking."""

    def __init__(self) -> None:
        self.node_id = str(uuid4())
        self.node_type = "TRADE_VALIDATION"
        self.name = "Trade Validation Node"

    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trade validation logic."""
        try:
            logger.info(f"Executing trade validation node: {self.node_id}")

            trade_data = state.get("data", {}).get("trades", [])
            if not trade_data:
                logger.warning("No trade data found in state")
                return {
                    **state,
                    "errors": state.get("errors", []) + ["No trade data provided"],
                }

            validation_results = []
            for trade in trade_data:
                validation_result = await self._validate_trade(trade)
                validation_results.append(validation_result)

            new_state = {
                **state,
                "data": {
                    **state.get("data", {}),
                    "validation_results": validation_results,
                    "validated_trades": [r for r in validation_results if r["status"] == "VALID"],
                    "failed_trades": [r for r in validation_results if r["status"] == "INVALID"],
                },
                "messages": state.get("messages", [])
                + [
                    {
                        "role": "system",
                        "content": f"Validated {len(trade_data)} trades",
                        "timestamp": datetime.utcnow().isoformat(),
                        "node_id": self.node_id,
                    }
                ],
            }

            logger.info(f"Trade validation completed: {len(validation_results)} trades processed")
            return new_state

        except Exception as e:
            logger.error(f"Trade validation node failed: {e}")
            return {
                **state,
                "errors": state.get("errors", []) + [f"Trade validation failed: {str(e)}"],
            }

    async def _validate_trade(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single trade."""
        trade_id = trade.get("id", "unknown")
        issues = []

        # Amount validation
        amount = trade.get("total_amount", 0)
        if amount > 10000000:  # $10M limit
            issues.append("Trade amount exceeds $10M limit")

        # Currency validation
        currency = trade.get("currency", "")
        valid_currencies = ["USD", "EUR", "GBP", "JPY", "CAD"]
        if currency not in valid_currencies:
            issues.append(f"Invalid currency: {currency}")

        # Settlement date validation
        settlement_date = trade.get("settlement_date")
        if not settlement_date:
            issues.append("Missing settlement date")

        return {
            "trade_id": trade_id,
            "status": "VALID" if not issues else "INVALID",
            "issues": issues,
            "validated_at": datetime.utcnow().isoformat()
        }


class LangGraphService:
    """Service for managing LangGraph workflows."""

    def __init__(self) -> None:
        self.graphs: Dict[str, Graph] = {}
        self.node_registry: Dict[str, Any] = {}
        self._register_default_nodes()

    def _register_default_nodes(self) -> None:
        """Register default LangGraph nodes."""
        self.node_registry["FIBO_MAPPING"] = FIBOPositionMappingNode
        self.node_registry["TRADE_VALIDATION"] = TradeValidationNode
        logger.info("Registered default LangGraph nodes")

    async def create_fibo_mapping_workflow(self) -> str:
        """Create a simple FIBO mapping workflow."""
        try:
            workflow_id = str(uuid4())

            workflow = StateGraph(dict)

            # Add nodes
            fibo_node = FIBOPositionMappingNode()
            workflow.add_node("fibo_mapping", fibo_node)

            workflow.set_entry_point("fibo_mapping")
            workflow.set_finish_point("fibo_mapping")

            compiled_graph = workflow.compile()

            self.graphs[workflow_id] = compiled_graph

            logger.info(f"Created FIBO mapping workflow: {workflow_id}")
            return workflow_id

        except Exception as e:
            logger.error(f"Failed to create FIBO mapping workflow: {e}")
            raise

    async def create_trade_validation_workflow(self) -> str:
        """Create a trade validation workflow."""
        try:
            workflow_id = str(uuid4())

            workflow = StateGraph(dict)

            # Add trade validation node
            validation_node = TradeValidationNode()
            workflow.add_node("trade_validation", validation_node)

            workflow.set_entry_point("trade_validation")
            workflow.set_finish_point("trade_validation")

            compiled_graph = workflow.compile()
            self.graphs[workflow_id] = compiled_graph

            logger.info(f"Created trade validation workflow: {workflow_id}")
            return workflow_id

        except Exception as e:
            logger.error(f"Failed to create trade validation workflow: {e}")
            raise

    async def execute_workflow(
        self, workflow_id: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a LangGraph workflow."""
        try:
            if workflow_id not in self.graphs:
                raise ValueError(f"Workflow {workflow_id} not found")

            graph = self.graphs[workflow_id]

            initial_state = {
                "data": input_data,
                "messages": [
                    {
                        "role": "system",
                        "content": f"Starting workflow execution: {workflow_id}",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ],
                "context": {
                    "workflow_id": workflow_id,
                    "execution_id": str(uuid4()),
                    "start_time": datetime.utcnow().isoformat(),
                },
                "errors": [],
            }

            logger.info(f"Executing LangGraph workflow: {workflow_id}")

            result = await graph.ainvoke(initial_state)

            if not isinstance(result, dict):
                result_dict: Dict[str, Any] = {
                    "data": result,
                    "context": {},
                    "messages": [],
                    "errors": [],
                }
            else:
                result_dict = dict(result)

            result_dict["context"]["end_time"] = datetime.utcnow().isoformat()
            result_dict["context"]["status"] = (
                "COMPLETED" if not result_dict.get("errors") else "FAILED"
            )

            logger.info(f"Workflow execution completed: {workflow_id}")
            return result_dict

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "context": {
                    "workflow_id": workflow_id,
                    "status": "ERROR",
                    "error": str(e),
                    "end_time": datetime.utcnow().isoformat(),
                },
                "errors": [str(e)],
                "messages": [
                    {
                        "role": "system",
                        "content": f"Workflow execution failed: {str(e)}",
                        "timestamp": datetime.utcnow().isoformat(),
                        "level": "ERROR",
                    }
                ],
            }

    async def get_workflow_info(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a workflow."""
        if workflow_id not in self.graphs:
            return None

        return {
            "workflow_id": workflow_id,
            "status": "ACTIVE",
            "node_count": len(self.graphs[workflow_id].nodes),
            "created_at": datetime.utcnow().isoformat(),
        }

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows."""
        return [
            {
                "workflow_id": workflow_id,
                "status": "ACTIVE",
                "node_count": len(graph.nodes),
            }
            for workflow_id, graph in self.graphs.items()
        ]

    def get_available_nodes(self) -> List[Dict[str, Any]]:
        """Get list of available node types."""
        return [
            {
                "node_type": node_type,
                "class_name": node_class.__name__,
                "description": getattr(
                    node_class, "__doc__", "No description available"
                ),
            }
            for node_type, node_class in self.node_registry.items()
        ]


langgraph_service = LangGraphService()


async def get_langgraph_service() -> LangGraphService:
    """Dependency injection for LangGraph service."""
    return langgraph_service
