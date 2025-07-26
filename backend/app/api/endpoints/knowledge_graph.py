from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.models.knowledge_graph import (
    Account,
    BaseEntity,
    DataStreamEntity,
    EntityType,
    GraphAnalytics,
    GraphTraversal,
    GraphVisualization,
    KnowledgeGraphQuery,
    MCPServerEntity,
    Position,
    RelationshipType,
    Security,
    Trade,
    WorkflowEntity,
)
from app.services.neo4j_service import Neo4jService, get_neo4j_service

router = APIRouter()


# Request/Response Models
class EntityCreateRequest(BaseModel):
    entity_type: EntityType
    properties: Dict[str, Any]


class EntityUpdateRequest(BaseModel):
    properties: Dict[str, Any]


class RelationshipCreateRequest(BaseModel):
    from_entity_id: str
    from_entity_type: EntityType
    to_entity_id: str
    to_entity_type: EntityType
    relationship_type: RelationshipType
    properties: Dict[str, Any] = {}


class GraphQueryRequest(BaseModel):
    cypher_query: str
    parameters: Dict[str, Any] = {}


class EntitySearchRequest(BaseModel):
    entity_types: Optional[List[EntityType]] = None
    search_term: Optional[str] = None
    filters: Dict[str, Any] = {}
    limit: int = 50


@router.get("/health")
async def health_check(neo4j_service: Neo4jService = Depends(get_neo4j_service)) -> Dict[str, Any]:
    """Check Neo4j connection health."""
    return {
        "status": "healthy" if neo4j_service.is_connected() else "unhealthy",
        "connected": neo4j_service.is_connected(),
    }


@router.get("/statistics")
async def get_graph_statistics(
    neo4j_service: Neo4jService = Depends(get_neo4j_service),
) -> Dict[str, Any]:
    """Get knowledge graph statistics."""
    try:
        stats = await neo4j_service.get_graph_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entities/")
async def create_entity(
    request: EntityCreateRequest,
    neo4j_service: Neo4jService = Depends(get_neo4j_service),
) -> Dict[str, Any]:
    """Create a new entity in the knowledge graph."""
    try:
        # Generate ID if not provided
        if "id" not in request.properties:
            request.properties["id"] = (
                f"{request.entity_type.value.lower()}_{uuid4().hex[:8]}"
            )

        entity = await neo4j_service.create_entity(
            entity_type=request.entity_type.value, properties=request.properties
        )
        return entity
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/entities/{entity_type}/{entity_id}")
async def get_entity(
    entity_type: EntityType,
    entity_id: str,
    neo4j_service: Neo4jService = Depends(get_neo4j_service),
) -> Dict[str, Any]:
    """Get a specific entity by type and ID."""
    try:
        entity = await neo4j_service.get_entity(entity_type.value, entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        return entity
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/entities/{entity_type}/{entity_id}")
async def update_entity(
    entity_type: EntityType,
    entity_id: str,
    request: EntityUpdateRequest,
    neo4j_service: Neo4jService = Depends(get_neo4j_service),
) -> Dict[str, Any]:
    """Update an existing entity."""
    try:
        entity = await neo4j_service.update_entity(
            entity_type=entity_type.value,
            entity_id=entity_id,
            properties=request.properties,
        )
        return entity
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/entities/{entity_type}/{entity_id}")
async def delete_entity(
    entity_type: EntityType,
    entity_id: str,
    neo4j_service: Neo4jService = Depends(get_neo4j_service),
) -> Dict[str, str]:
    """Delete an entity and all its relationships."""
    try:
        success = await neo4j_service.delete_entity(entity_type.value, entity_id)
        if not success:
            raise HTTPException(status_code=404, detail="Entity not found")
        return {"message": "Entity deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/relationships/")
async def create_relationship(
    request: RelationshipCreateRequest,
    neo4j_service: Neo4jService = Depends(get_neo4j_service),
) -> Dict[str, Any]:
    """Create a relationship between two entities."""
    try:
        relationship = await neo4j_service.create_relationship(
            from_entity_type=request.from_entity_type.value,
            from_entity_id=request.from_entity_id,
            to_entity_type=request.to_entity_type.value,
            to_entity_id=request.to_entity_id,
            relationship_type=request.relationship_type.value,
            properties=request.properties,
        )
        return relationship
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/entities/{entity_type}/{entity_id}/relationships")
async def get_entity_relationships(
    entity_type: EntityType,
    entity_id: str,
    direction: str = Query("both", regex="^(incoming|outgoing|both)$"),
    neo4j_service: Neo4jService = Depends(get_neo4j_service),
) -> Dict[str, Any]:
    """Get all relationships for an entity."""
    try:
        relationships = await neo4j_service.get_relationships(
            entity_type=entity_type.value, entity_id=entity_id, direction=direction
        )
        return {"entity_id": entity_id, "relationships": relationships}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/cypher")
async def execute_cypher_query(
    request: GraphQueryRequest, neo4j_service: Neo4jService = Depends(get_neo4j_service)
) -> Dict[str, Any]:
    """Execute a custom Cypher query."""
    try:
        # Basic security check - restrict certain operations
        forbidden_keywords = [
            "DELETE",
            "DETACH",
            "REMOVE",
            "DROP",
            "CREATE INDEX",
            "CREATE CONSTRAINT",
        ]
        query_upper = request.cypher_query.upper()

        for keyword in forbidden_keywords:
            if keyword in query_upper:
                raise HTTPException(
                    status_code=403,
                    detail=f"Query contains forbidden operation: {keyword}",
                )

        results = await neo4j_service.execute_cypher(
            query=request.cypher_query, parameters=request.parameters
        )
        return {"results": results, "count": len(results)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/search/entities")
async def search_entities(
    request: EntitySearchRequest,
    neo4j_service: Neo4jService = Depends(get_neo4j_service),
) -> Dict[str, Any]:
    """Search for entities based on criteria."""
    try:
        # Build dynamic query based on search criteria
        where_clauses = []
        parameters = {}

        if request.entity_types:
            # Create label filter
            labels = [f"n:{et.value}" for et in request.entity_types]
            label_filter = " OR ".join(labels)
            where_clauses.append(f"({label_filter})")

        if request.search_term:
            where_clauses.append(
                "(n.name CONTAINS $search_term OR n.description CONTAINS $search_term)"
            )
            parameters["search_term"] = request.search_term

        # Add custom filters
        for key, value in request.filters.items():
            where_clauses.append(f"n.{key} = ${key}")
            parameters[key] = value

        where_clause = " AND ".join(where_clauses) if where_clauses else "true"

        query = f"""
        MATCH (n)
        WHERE {where_clause}
        RETURN n, labels(n) as labels
        LIMIT $limit
        """
        parameters["limit"] = str(request.limit)

        results = await neo4j_service.execute_cypher(query, parameters)

        entities = []
        for record in results:
            entity_data = record["n"]
            entity_data["entity_labels"] = record["labels"]
            entities.append(entity_data)

        return {"entities": entities, "count": len(entities)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualization/graph")
async def get_graph_visualization(
    center_entity_id: Optional[str] = None,
    entity_types: Optional[List[EntityType]] = Query(None),
    depth: int = Query(2, ge=1, le=5),
    limit: int = Query(100, ge=1, le=500),
    neo4j_service: Neo4jService = Depends(get_neo4j_service),
) -> Dict[str, Any]:
    """Get graph data for visualization."""
    try:
        if center_entity_id:
            # Get subgraph around a specific entity
            query = f"""
            MATCH (center {{id: $center_id}})
            CALL apoc.path.subgraphNodes(center, {{
                maxLevel: $depth,
                limit: $limit
            }}) YIELD node
            MATCH (node)-[r]-(connected)
            WHERE connected IN apoc.path.subgraphNodes(center, {{maxLevel: $depth, limit: $limit}})
            RETURN DISTINCT node, r, connected, labels(node) as node_labels, labels(connected) as connected_labels
            """
            parameters = {"center_id": center_entity_id, "depth": depth, "limit": limit}
        else:
            # Get general overview of the graph
            type_filter = ""
            if entity_types:
                labels = [f"n:{et.value}" for et in entity_types]
                type_filter = f"WHERE ({' OR '.join(labels)})"

            query = f"""
            MATCH (n)-[r]-(m)
            {type_filter}
            RETURN n, r, m, labels(n) as n_labels, labels(m) as m_labels
            LIMIT $limit
            """
            parameters = {"limit": limit}

        results = await neo4j_service.execute_cypher(query, parameters)

        # Process results into visualization format
        nodes = {}
        edges = []

        for record in results:
            # Add nodes
            for node_key in ["node", "n", "connected", "m"]:
                if node_key in record and record[node_key]:
                    node_data = record[node_key]
                    node_id = node_data.get("id")
                    if node_id and node_id not in nodes:
                        label_key = (
                            f"{node_key}_labels"
                            if f"{node_key}_labels" in record
                            else "node_labels"
                        )
                        labels = record.get(label_key, [])

                        nodes[node_id] = {
                            "id": node_id,
                            "label": node_data.get("name", node_id),
                            "type": labels[0] if labels else "Unknown",
                            "properties": node_data,
                        }

            # Add relationship
            if "r" in record and record["r"]:
                rel_data = record["r"]
                source_id = None
                target_id = None

                # Determine source and target
                if "node" in record and "connected" in record:
                    source_id = record["node"].get("id")
                    target_id = record["connected"].get("id")
                elif "n" in record and "m" in record:
                    source_id = record["n"].get("id")
                    target_id = record["m"].get("id")

                if source_id and target_id:
                    edges.append(
                        {
                            "source": source_id,
                            "target": target_id,
                            "type": rel_data.get("type", "RELATED"),
                            "properties": dict(rel_data),
                        }
                    )

        return {
            "nodes": list(nodes.values()),
            "edges": edges,
            "summary": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "center_entity": center_entity_id,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/centrality")
async def get_centrality_analysis(
    entity_type: Optional[EntityType] = None,
    limit: int = Query(20, ge=1, le=100),
    neo4j_service: Neo4jService = Depends(get_neo4j_service),
) -> Dict[str, Any]:
    """Get centrality analysis for entities."""
    try:
        type_filter = f":{entity_type.value}" if entity_type else ""

        # Use Graph Data Science algorithms if available, otherwise simple degree centrality
        query = f"""
        MATCH (n{type_filter})-[r]-(m)
        WITH n, count(r) as degree
        ORDER BY degree DESC
        LIMIT $limit
        RETURN n.id as entity_id, n.name as entity_name, labels(n) as labels, degree
        """

        results = await neo4j_service.execute_cypher(query, {"limit": limit})

        centrality_data = []
        for record in results:
            centrality_data.append(
                {
                    "entity_id": record["entity_id"],
                    "entity_name": record["entity_name"],
                    "entity_type": (
                        record["labels"][0] if record["labels"] else "Unknown"
                    ),
                    "degree_centrality": record["degree"],
                }
            )

        return {"centrality_analysis": centrality_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/shortest-path")
async def get_shortest_path(
    from_entity_id: str,
    to_entity_id: str,
    max_depth: int = Query(6, ge=1, le=10),
    neo4j_service: Neo4jService = Depends(get_neo4j_service),
) -> Dict[str, Any]:
    """Find shortest path between two entities."""
    try:
        query = """
        MATCH (start {id: $from_id}), (end {id: $to_id})
        MATCH path = shortestPath((start)-[*1..15]-(end))
        RETURN path, length(path) as path_length
        """

        results = await neo4j_service.execute_cypher(
            query,
            {"from_id": from_entity_id, "to_id": to_entity_id, "max_depth": max_depth},
        )

        if not results:
            return {"path": None, "message": "No path found between entities"}

        # Process the path
        path_data = results[0]
        path_length = path_data["path_length"]

        return {
            "from_entity_id": from_entity_id,
            "to_entity_id": to_entity_id,
            "path_length": path_length,
            "path_found": True,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
