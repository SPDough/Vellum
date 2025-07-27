from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.fibo_ontology import FIBOOntologyQuery
from app.services.fibo_service import get_fibo_service, FIBOService

router = APIRouter()


@router.get("/entities", response_model=List[Dict[str, Any]])
async def list_fibo_entities(
    entity_type: Optional[str] = Query(None, description="Filter by FIBO entity type"),
    limit: Optional[int] = Query(100, description="Maximum number of entities to return"),
    fibo_service: FIBOService = Depends(get_fibo_service),
) -> List[Dict[str, Any]]:
    """List FIBO ontology entities."""
    try:
        query = FIBOOntologyQuery(
            entity_types=[entity_type] if entity_type else None,
            limit=limit,
        )
        
        entities = await fibo_service.query_fibo_entities(query)
        return entities

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list FIBO entities: {str(e)}",
        )


@router.get("/mappings", response_model=List[Dict[str, Any]])
async def get_entity_mappings(
    original_type: Optional[str] = Query(None, description="Filter by original entity type"),
    fibo_type: Optional[str] = Query(None, description="Filter by FIBO entity type"),
    fibo_service: FIBOService = Depends(get_fibo_service),
) -> List[Dict[str, Any]]:
    """Get entity mappings between original and FIBO entities."""
    try:
        query = FIBOOntologyQuery(
            entity_types=["FIBOEntityMapping"],
            property_filters={},
        )
        
        if original_type:
            query.property_filters["original_entity_type"] = original_type
        if fibo_type:
            query.property_filters["fibo_entity_type"] = fibo_type
        
        mappings = await fibo_service.query_fibo_entities(query)
        return mappings

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get entity mappings: {str(e)}",
        )


@router.post("/mappings", response_model=Dict[str, Any])
async def create_entity_mapping(
    entity_type: str,
    entity_id: str,
    fibo_type: str,
    fibo_service: FIBOService = Depends(get_fibo_service),
) -> Dict[str, Any]:
    """Create a mapping between an existing entity and FIBO ontology."""
    try:
        result = await fibo_service.map_entity_to_fibo(entity_type, entity_id, fibo_type)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entity {entity_type}:{entity_id} not found or mapping failed",
            )
        
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create entity mapping: {str(e)}",
        )


@router.post("/query", response_model=List[Dict[str, Any]])
async def query_fibo_entities(
    query: FIBOOntologyQuery,
    fibo_service: FIBOService = Depends(get_fibo_service),
) -> List[Dict[str, Any]]:
    """Execute a flexible query against FIBO entities."""
    try:
        entities = await fibo_service.query_fibo_entities(query)
        return entities

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query FIBO entities: {str(e)}",
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_fibo_statistics(
    fibo_service: FIBOService = Depends(get_fibo_service),
) -> Dict[str, Any]:
    """Get statistics about FIBO entities in the knowledge graph."""
    try:
        stats = await fibo_service.get_fibo_statistics()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get FIBO statistics: {str(e)}",
        )
