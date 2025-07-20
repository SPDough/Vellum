import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.services.neo4j_service import Neo4jService, get_neo4j_service
from app.services.mcp_service import MCPService, get_mcp_service
from app.models.knowledge_graph import EntityType, RelationshipType

logger = logging.getLogger(__name__)


class KnowledgeGraphSyncService:
    """Service to synchronize data between operational systems and knowledge graph."""
    
    def __init__(self):
        self.neo4j_service: Optional[Neo4jService] = None
        self.mcp_service: Optional[MCPService] = None
        self.sync_tasks = {}
        
    async def initialize(self):
        """Initialize the sync service with dependencies."""
        self.neo4j_service = await get_neo4j_service()
        self.mcp_service = await get_mcp_service()
    
    async def sync_mcp_servers_to_graph(self) -> int:
        """Sync MCP server information to the knowledge graph."""
        try:
            logger.info("Syncing MCP servers to knowledge graph...")
            
            # Get all MCP servers from the service
            servers = await self.mcp_service.list_servers()
            synced_count = 0
            
            for server in servers:
                try:
                    # Create or update MCP server entity
                    server_properties = {
                        "id": server["id"],
                        "name": server["name"],
                        "server_url": server["base_url"],
                        "provider_type": server["provider_type"],
                        "auth_type": server["auth_type"],
                        "capabilities": server.get("capabilities", []),
                        "status": server.get("status", "UNKNOWN"),
                        "version": server.get("version"),
                        "description": server.get("description"),
                        "enabled": server.get("enabled", True),
                        "last_sync": datetime.utcnow().isoformat()
                    }
                    
                    # Check if entity exists
                    existing = await self.neo4j_service.get_entity(
                        EntityType.MCP_SERVER.value, 
                        server["id"]
                    )
                    
                    if existing:
                        await self.neo4j_service.update_entity(
                            EntityType.MCP_SERVER.value,
                            server["id"],
                            server_properties
                        )
                    else:
                        await self.neo4j_service.create_entity(
                            EntityType.MCP_SERVER.value,
                            server_properties
                        )
                    
                    synced_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to sync MCP server {server.get('id', 'unknown')}: {e}")
            
            logger.info(f"Successfully synced {synced_count} MCP servers to knowledge graph")
            return synced_count
            
        except Exception as e:
            logger.error(f"Failed to sync MCP servers to knowledge graph: {e}")
            return 0
    
    async def sync_workflows_to_graph(self, workflows: List[Dict[str, Any]]) -> int:
        """Sync workflow information to the knowledge graph."""
        try:
            logger.info("Syncing workflows to knowledge graph...")
            synced_count = 0
            
            for workflow in workflows:
                try:
                    # Create or update workflow entity
                    workflow_properties = {
                        "id": workflow["id"],
                        "name": workflow["name"],
                        "description": workflow.get("description"),
                        "workflow_type": workflow.get("workflow_type", "CUSTOM"),
                        "status": workflow.get("status", "DRAFT"),
                        "trigger_schedule": workflow.get("execution_settings", {}).get("schedule"),
                        "last_execution": workflow.get("last_executed"),
                        "version": workflow.get("version", 1),
                        "enabled": workflow.get("enabled", True),
                        "last_sync": datetime.utcnow().isoformat()
                    }
                    
                    # Check if entity exists
                    existing = await self.neo4j_service.get_entity(
                        EntityType.WORKFLOW.value, 
                        workflow["id"]
                    )
                    
                    if existing:
                        await self.neo4j_service.update_entity(
                            EntityType.WORKFLOW.value,
                            workflow["id"],
                            workflow_properties
                        )
                    else:
                        await self.neo4j_service.create_entity(
                            EntityType.WORKFLOW.value,
                            workflow_properties
                        )
                    
                    # Create relationships between workflows and MCP servers
                    await self._create_workflow_mcp_relationships(workflow)
                    
                    synced_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to sync workflow {workflow.get('id', 'unknown')}: {e}")
            
            logger.info(f"Successfully synced {synced_count} workflows to knowledge graph")
            return synced_count
            
        except Exception as e:
            logger.error(f"Failed to sync workflows to knowledge graph: {e}")
            return 0
    
    async def _create_workflow_mcp_relationships(self, workflow: Dict[str, Any]):
        """Create relationships between workflow and MCP servers it uses."""
        try:
            workflow_id = workflow["id"]
            
            # Look for MCP server references in workflow nodes
            for node in workflow.get("nodes", []):
                if node.get("type") == "MCP_CALL":
                    mcp_server_id = node.get("config", {}).get("mcp_server_id")
                    if mcp_server_id:
                        # Check if MCP server exists in graph
                        mcp_entity = await self.neo4j_service.get_entity(
                            EntityType.MCP_SERVER.value, 
                            mcp_server_id
                        )
                        
                        if mcp_entity:
                            # Create relationship
                            await self.neo4j_service.create_relationship(
                                from_entity_type=EntityType.WORKFLOW.value,
                                from_entity_id=workflow_id,
                                to_entity_type=EntityType.MCP_SERVER.value,
                                to_entity_id=mcp_server_id,
                                relationship_type=RelationshipType.CONNECTS_TO.value,
                                properties={
                                    "tool_name": node.get("config", {}).get("endpoint_id"),
                                    "created_at": datetime.utcnow().isoformat()
                                }
                            )
                            
        except Exception as e:
            logger.error(f"Failed to create workflow-MCP relationships: {e}")
    
    async def sync_data_streams_to_graph(self, data_streams: List[Dict[str, Any]]) -> int:
        """Sync data stream information to the knowledge graph."""
        try:
            logger.info("Syncing data streams to knowledge graph...")
            synced_count = 0
            
            for stream in data_streams:
                try:
                    # Create or update data stream entity
                    stream_properties = {
                        "id": stream["id"],
                        "name": stream["name"],
                        "description": stream.get("description"),
                        "data_type": stream["data_type"],
                        "source_system": stream.get("source_mcp_server_id", "unknown"),
                        "target_systems": stream.get("subscribers", []),
                        "status": stream.get("status", "INACTIVE"),
                        "throughput_rps": stream.get("records_per_second"),
                        "latency_ms": stream.get("latency_ms"),
                        "buffer_size": stream.get("buffer_size"),
                        "last_sync": datetime.utcnow().isoformat()
                    }
                    
                    # Check if entity exists
                    existing = await self.neo4j_service.get_entity(
                        EntityType.DATA_STREAM.value, 
                        stream["id"]
                    )
                    
                    if existing:
                        await self.neo4j_service.update_entity(
                            EntityType.DATA_STREAM.value,
                            stream["id"],
                            stream_properties
                        )
                    else:
                        await self.neo4j_service.create_entity(
                            EntityType.DATA_STREAM.value,
                            stream_properties
                        )
                    
                    # Create relationship with source MCP server
                    source_mcp_id = stream.get("source_mcp_server_id")
                    if source_mcp_id:
                        await self.neo4j_service.create_relationship(
                            from_entity_type=EntityType.MCP_SERVER.value,
                            from_entity_id=source_mcp_id,
                            to_entity_type=EntityType.DATA_STREAM.value,
                            to_entity_id=stream["id"],
                            relationship_type=RelationshipType.PROVIDES_DATA.value,
                            properties={
                                "data_type": stream["data_type"],
                                "created_at": datetime.utcnow().isoformat()
                            }
                        )
                    
                    synced_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to sync data stream {stream.get('id', 'unknown')}: {e}")
            
            logger.info(f"Successfully synced {synced_count} data streams to knowledge graph")
            return synced_count
            
        except Exception as e:
            logger.error(f"Failed to sync data streams to knowledge graph: {e}")
            return 0
    
    async def create_sample_financial_data(self):
        """Create sample financial entities for demonstration."""
        try:
            logger.info("Creating sample financial data in knowledge graph...")
            
            # Sample accounts
            accounts = [
                {
                    "id": "acc_global_equity",
                    "name": "Global Equity Fund",
                    "account_number": "GEF001",
                    "account_type": "CUSTODY",
                    "base_currency": "USD",
                    "status": "ACTIVE"
                },
                {
                    "id": "acc_fixed_income",
                    "name": "Fixed Income Fund",
                    "account_number": "FIF001", 
                    "account_type": "CUSTODY",
                    "base_currency": "USD",
                    "status": "ACTIVE"
                }
            ]
            
            # Sample securities
            securities = [
                {
                    "id": "sec_aapl",
                    "name": "Apple Inc.",
                    "symbol": "AAPL",
                    "isin": "US0378331005",
                    "security_type": "EQUITY",
                    "currency": "USD",
                    "exchange": "NASDAQ",
                    "sector": "Technology"
                },
                {
                    "id": "sec_googl",
                    "name": "Alphabet Inc.",
                    "symbol": "GOOGL",
                    "isin": "US02079K3059",
                    "security_type": "EQUITY",
                    "currency": "USD",
                    "exchange": "NASDAQ",
                    "sector": "Technology"
                }
            ]
            
            # Create entities
            for account in accounts:
                await self.neo4j_service.create_entity(EntityType.ACCOUNT.value, account)
            
            for security in securities:
                await self.neo4j_service.create_entity(EntityType.SECURITY.value, security)
            
            # Create sample positions (relationships)
            positions = [
                {
                    "account_id": "acc_global_equity",
                    "security_id": "sec_aapl",
                    "quantity": 5000,
                    "market_value": 750000.00,
                    "book_cost": 725000.00
                },
                {
                    "account_id": "acc_global_equity",
                    "security_id": "sec_googl",
                    "quantity": 2000,
                    "market_value": 280000.00,
                    "book_cost": 275000.00
                }
            ]
            
            for position in positions:
                await self.neo4j_service.create_relationship(
                    from_entity_type=EntityType.ACCOUNT.value,
                    from_entity_id=position["account_id"],
                    to_entity_type=EntityType.SECURITY.value,
                    to_entity_id=position["security_id"],
                    relationship_type=RelationshipType.HOLDS.value,
                    properties={
                        "quantity": position["quantity"],
                        "market_value": position["market_value"],
                        "book_cost": position["book_cost"],
                        "as_of_date": datetime.utcnow().isoformat()
                    }
                )
            
            logger.info("Successfully created sample financial data")
            
        except Exception as e:
            logger.error(f"Failed to create sample financial data: {e}")
    
    async def sync_all_data(self):
        """Sync all data sources to the knowledge graph."""
        try:
            logger.info("Starting full knowledge graph sync...")
            
            # Sync MCP servers
            mcp_count = await self.sync_mcp_servers_to_graph()
            
            # Create sample data for demonstration
            await self.create_sample_financial_data()
            
            logger.info(f"Knowledge graph sync completed. Synced {mcp_count} MCP servers")
            
        except Exception as e:
            logger.error(f"Failed to sync all data to knowledge graph: {e}")


# Global sync service instance
kg_sync_service = KnowledgeGraphSyncService()