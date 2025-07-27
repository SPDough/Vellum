import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from neo4j import AsyncGraphDatabase, GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable

from app.core.config import get_settings
from app.core.telemetry import get_tracer

logger = logging.getLogger(__name__)
tracer = get_tracer("neo4j_service")
settings = get_settings()


class Neo4jService:
    """Service for Neo4j knowledge graph operations."""

    def __init__(self) -> None:
        self.driver = None
        self.connected = False

    async def connect(self) -> None:
        """Initialize connection to Neo4j database."""
        try:
            logger.info("Connecting to Neo4j...")

            # Create async driver
            self.driver = AsyncGraphDatabase.driver(
                settings.neo4j_url,
                auth=(settings.neo4j_user, settings.neo4j_password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60,
            )

            # Test the connection
            await self._verify_connectivity()

            # Initialize schema and constraints
            await self._initialize_schema()

            self.connected = True
            logger.info("Successfully connected to Neo4j")

        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def disconnect(self) -> None:
        """Close Neo4j driver."""
        if self.driver:
            await self.driver.close()
            self.connected = False
            logger.info("Disconnected from Neo4j")

    async def _verify_connectivity(self) -> None:
        """Verify that we can connect to Neo4j."""
        if not self.driver:
            raise Exception("Neo4j driver not initialized")
        async with self.driver.session() as session:
            result = await session.run("RETURN 1 as test")
            record = await result.single()
            if record["test"] != 1:
                raise Exception("Neo4j connectivity test failed")

    async def _initialize_schema(self) -> None:
        """Initialize Neo4j schema with constraints and indexes."""
        with tracer.start_as_current_span("neo4j_initialize_schema"):
            try:
                if not self.driver:
                    raise Exception("Neo4j driver not initialized")
                async with self.driver.session() as session:
                    # Create constraints for unique identifiers
                    constraints = [
                        "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
                        "CREATE CONSTRAINT account_id_unique IF NOT EXISTS FOR (a:Account) REQUIRE a.id IS UNIQUE",
                        "CREATE CONSTRAINT trade_id_unique IF NOT EXISTS FOR (t:Trade) REQUIRE t.id IS UNIQUE",
                        "CREATE CONSTRAINT position_id_unique IF NOT EXISTS FOR (p:Position) REQUIRE p.id IS UNIQUE",
                        "CREATE CONSTRAINT security_id_unique IF NOT EXISTS FOR (s:Security) REQUIRE s.id IS UNIQUE",
                        "CREATE CONSTRAINT mcp_server_id_unique IF NOT EXISTS FOR (m:MCPServer) REQUIRE m.id IS UNIQUE",
                        "CREATE CONSTRAINT workflow_id_unique IF NOT EXISTS FOR (w:Workflow) REQUIRE w.id IS UNIQUE",
                        "CREATE CONSTRAINT data_stream_id_unique IF NOT EXISTS FOR (d:DataStream) REQUIRE d.id IS UNIQUE",
                    ]

                    for constraint in constraints:
                        try:
                            await session.run(constraint)
                        except Exception as e:
                            # Constraint might already exist
                            logger.debug(f"Constraint creation note: {e}")

                    # Create indexes for frequently queried properties
                    indexes = [
                        "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.type)",
                        "CREATE INDEX account_name_idx IF NOT EXISTS FOR (a:Account) ON (a.name)",
                        "CREATE INDEX trade_date_idx IF NOT EXISTS FOR (t:Trade) ON (t.trade_date)",
                        "CREATE INDEX security_symbol_idx IF NOT EXISTS FOR (s:Security) ON (s.symbol)",
                        "CREATE INDEX workflow_status_idx IF NOT EXISTS FOR (w:Workflow) ON (w.status)",
                        "CREATE INDEX data_stream_status_idx IF NOT EXISTS FOR (d:DataStream) ON (d.status)",
                    ]

                    for index in indexes:
                        try:
                            await session.run(index)
                        except Exception as e:
                            logger.debug(f"Index creation note: {e}")

                    logger.info("Neo4j schema initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize Neo4j schema: {e}")
                raise

    async def create_entity(
        self, entity_type: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new entity in the knowledge graph."""
        with tracer.start_as_current_span("neo4j_create_entity") as span:
            span.set_attributes(
                {
                    "neo4j.entity_type": entity_type,
                    "neo4j.properties_count": len(properties),
                }
            )

            try:
                properties["created_at"] = datetime.utcnow().isoformat()
                properties["updated_at"] = datetime.utcnow().isoformat()

                query = f"""
                CREATE (e:{entity_type} $properties)
                RETURN e
                """

                if not self.driver:
                    raise Exception("Neo4j driver not initialized")
                async with self.driver.session() as session:
                    result = await session.run(query, properties=properties)
                    record = await result.single()

                    if record:
                        entity = dict(record["e"])
                        span.set_attribute("neo4j.success", True)
                        return entity

                    raise Exception("Failed to create entity")

            except Exception as e:
                span.set_attribute("neo4j.success", False)
                span.record_exception(e)
                logger.error(f"Failed to create entity: {e}")
                raise

    async def get_entity(
        self, entity_type: str, entity_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve an entity by type and ID."""
        with tracer.start_as_current_span("neo4j_get_entity") as span:
            span.set_attributes(
                {"neo4j.entity_type": entity_type, "neo4j.entity_id": entity_id}
            )

            try:
                query = f"""
                MATCH (e:{entity_type} {{id: $entity_id}})
                RETURN e
                """

                if not self.driver:
                    return None
                async with self.driver.session() as session:
                    result = await session.run(query, entity_id=entity_id)
                    record = await result.single()

                    if record:
                        entity = dict(record["e"])
                        span.set_attribute("neo4j.success", True)
                        return entity

                    return None

            except Exception as e:
                span.set_attribute("neo4j.success", False)
                span.record_exception(e)
                logger.error(f"Failed to get entity: {e}")
                raise

    async def update_entity(
        self, entity_type: str, entity_id: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing entity."""
        with tracer.start_as_current_span("neo4j_update_entity") as span:
            span.set_attributes(
                {"neo4j.entity_type": entity_type, "neo4j.entity_id": entity_id}
            )

            try:
                properties["updated_at"] = datetime.utcnow().isoformat()

                # Build SET clause for properties
                set_clauses = [
                    f"e.{key} = $properties.{key}" for key in properties.keys()
                ]
                set_clause = ", ".join(set_clauses)

                query = f"""
                MATCH (e:{entity_type} {{id: $entity_id}})
                SET {set_clause}
                RETURN e
                """

                if not self.driver:
                    raise Exception("Neo4j driver not initialized")
                async with self.driver.session() as session:
                    result = await session.run(
                        query, entity_id=entity_id, properties=properties
                    )
                    record = await result.single()

                    if record:
                        entity = dict(record["e"])
                        span.set_attribute("neo4j.success", True)
                        return entity

                    raise Exception("Entity not found")

            except Exception as e:
                span.set_attribute("neo4j.success", False)
                span.record_exception(e)
                logger.error(f"Failed to update entity: {e}")
                raise

    async def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """Delete an entity and all its relationships."""
        with tracer.start_as_current_span("neo4j_delete_entity") as span:
            span.set_attributes(
                {"neo4j.entity_type": entity_type, "neo4j.entity_id": entity_id}
            )

            try:
                query = f"""
                MATCH (e:{entity_type} {{id: $entity_id}})
                DETACH DELETE e
                RETURN count(e) as deleted_count
                """

                if not self.driver:
                    return False
                async with self.driver.session() as session:
                    result = await session.run(query, entity_id=entity_id)
                    record = await result.single()

                    deleted_count = record["deleted_count"] if record else 0
                    success = deleted_count > 0

                    span.set_attribute("neo4j.success", success)
                    return success

            except Exception as e:
                span.set_attribute("neo4j.success", False)
                span.record_exception(e)
                logger.error(f"Failed to delete entity: {e}")
                raise

    async def create_relationship(
        self,
        from_entity_type: str,
        from_entity_id: str,
        to_entity_type: str,
        to_entity_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a relationship between two entities."""
        with tracer.start_as_current_span("neo4j_create_relationship") as span:
            span.set_attributes(
                {
                    "neo4j.from_type": from_entity_type,
                    "neo4j.to_type": to_entity_type,
                    "neo4j.relationship_type": relationship_type,
                }
            )

            try:
                rel_properties = properties or {}
                rel_properties["created_at"] = datetime.utcnow().isoformat()

                query = f"""
                MATCH (from:{from_entity_type} {{id: $from_id}})
                MATCH (to:{to_entity_type} {{id: $to_id}})
                CREATE (from)-[r:{relationship_type} $rel_properties]->(to)
                RETURN r
                """

                if not self.driver:
                    raise Exception("Neo4j driver not initialized")
                async with self.driver.session() as session:
                    result = await session.run(
                        query,
                        from_id=from_entity_id,
                        to_id=to_entity_id,
                        rel_properties=rel_properties,
                    )
                    record = await result.single()

                    if record:
                        relationship = dict(record["r"])
                        span.set_attribute("neo4j.success", True)
                        return relationship

                    raise Exception("Failed to create relationship")

            except Exception as e:
                span.set_attribute("neo4j.success", False)
                span.record_exception(e)
                logger.error(f"Failed to create relationship: {e}")
                raise

    async def get_relationships(
        self, entity_type: str, entity_id: str, direction: str = "both"
    ) -> List[Dict[str, Any]]:
        """Get all relationships for an entity."""
        with tracer.start_as_current_span("neo4j_get_relationships") as span:
            span.set_attributes(
                {
                    "neo4j.entity_type": entity_type,
                    "neo4j.entity_id": entity_id,
                    "neo4j.direction": direction,
                }
            )

            try:
                if direction == "outgoing":
                    pattern = "(e)-[r]->(other)"
                elif direction == "incoming":
                    pattern = "(other)-[r]->(e)"
                else:  # both
                    pattern = "(e)-[r]-(other)"

                query = f"""
                MATCH (e:{entity_type} {{id: $entity_id}})
                MATCH {pattern}
                RETURN r, other, labels(other) as other_labels
                """

                if not self.driver:
                    return []
                async with self.driver.session() as session:
                    result = await session.run(query, entity_id=entity_id)

                    relationships = []
                    async for record in result:
                        rel_data = {
                            "relationship": dict(record["r"]),
                            "other_entity": dict(record["other"]),
                            "other_entity_labels": record["other_labels"],
                        }
                        relationships.append(rel_data)

                    span.set_attribute("neo4j.success", True)
                    span.set_attribute("neo4j.relationships_count", len(relationships))
                    return relationships

            except Exception as e:
                span.set_attribute("neo4j.success", False)
                span.record_exception(e)
                logger.error(f"Failed to get relationships: {e}")
                raise

    async def execute_cypher(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a custom Cypher query."""
        with tracer.start_as_current_span("neo4j_execute_cypher") as span:
            span.set_attribute("neo4j.query_length", len(query))

            try:
                if not self.driver:
                    return []
                async with self.driver.session() as session:
                    result = await session.run(query, parameters or {})

                    records = []
                    async for record in result:
                        records.append(dict(record))

                    span.set_attribute("neo4j.success", True)
                    span.set_attribute("neo4j.records_count", len(records))
                    return records

            except Exception as e:
                span.set_attribute("neo4j.success", False)
                span.record_exception(e)
                logger.error(f"Failed to execute Cypher query: {e}")
                raise

    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get general statistics about the knowledge graph."""
        try:
            stats_queries = {
                "total_nodes": "MATCH (n) RETURN count(n) as count",
                "total_relationships": "MATCH ()-[r]->() RETURN count(r) as count",
                "node_types": "MATCH (n) RETURN labels(n)[0] as label, count(*) as count ORDER BY count DESC",
                "relationship_types": "MATCH ()-[r]->() RETURN type(r) as type, count(*) as count ORDER BY count DESC",
            }

            statistics: Dict[str, Any] = {}

            if not self.driver:
                return {}
            async with self.driver.session() as session:
                # Get simple counts
                for stat_name, query in stats_queries.items():
                    if stat_name in ["total_nodes", "total_relationships"]:
                        result = await session.run(query)
                        record = await result.single()
                        statistics[stat_name] = record["count"] if record else 0
                    else:
                        result = await session.run(query)
                        records = []
                        async for record in result:
                            records.append(dict(record))
                        statistics[stat_name] = records

            return statistics

        except Exception as e:
            logger.error(f"Failed to get graph statistics: {e}")
            return {}

    def is_connected(self) -> bool:
        """Check if connected to Neo4j."""
        return self.connected


# Global Neo4j service instance
neo4j_service = Neo4jService()


async def get_neo4j_service() -> Neo4jService:
    """Dependency injection for Neo4j service."""
    return neo4j_service
