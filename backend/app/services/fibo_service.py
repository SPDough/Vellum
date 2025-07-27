import logging
from typing import Any, Dict, List, Optional

from app.models.fibo_ontology import (
    FIBOOntologyMapping,
    FIBOQuery,
    FIBOLegalEntity,
    FIBOEquityInstrument,
    FIBOFinancialAccount,
    FIBOPositionHolding,
    FIBOTradeTransaction,
)
from app.services.neo4j_service import Neo4jService, get_neo4j_service

logger = logging.getLogger(__name__)


class FIBOService:
    """Service for FIBO ontology operations and entity mapping."""

    def __init__(self, neo4j_service: Neo4jService):
        self.neo4j_service = neo4j_service

    async def map_entity_to_fibo(
        self, entity_type: str, entity_id: str, fibo_type: str
    ) -> Optional[Dict[str, Any]]:
        """Map an existing knowledge graph entity to FIBO ontology."""
        try:
            original_entity = await self.neo4j_service.get_entity(entity_type, entity_id)
            if not original_entity:
                logger.warning(f"Entity {entity_type}:{entity_id} not found")
                return None

            if fibo_type == "FIBOLegalEntity" and entity_type == "Custodian":
                return await self._map_custodian_to_fibo_legal_entity(original_entity)
            elif fibo_type == "FIBOEquityInstrument" and entity_type == "Security":
                return await self._map_security_to_fibo_equity(original_entity)
            elif fibo_type == "FIBOFinancialAccount" and entity_type == "Account":
                return await self._map_account_to_fibo_account(original_entity)
            elif fibo_type == "FIBOPositionHolding" and entity_type == "Position":
                return await self._map_position_to_fibo_holding(original_entity)
            else:
                logger.warning(f"Unsupported mapping: {entity_type} -> {fibo_type}")
                return None

        except Exception as e:
            logger.error(f"Failed to map entity to FIBO: {e}")
            return None

    async def _map_custodian_to_fibo_legal_entity(
        self, custodian: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map a Custodian entity to FIBOLegalEntity."""
        fibo_entity = FIBOLegalEntity(
            id=f"fibo-{custodian['id']}",
            name=custodian.get("name", "Unknown Legal Entity"),
            fibo_type="LegalEntity",
            legal_name=custodian.get("name", "Unknown Legal Entity"),
            jurisdiction=custodian.get("jurisdiction", "UNKNOWN"),
            lei_code=custodian.get("lei_code"),
            regulatory_status=custodian.get("status", "UNKNOWN"),
            business_registry_identifier=custodian.get("registry_id"),
        )

        created_entity = await self.neo4j_service.create_entity(
            "FIBOLegalEntity", fibo_entity.dict()
        )

        await self._create_entity_mapping(
            custodian["id"], "Custodian", created_entity["id"], "FIBOLegalEntity"
        )

        return created_entity

    async def _map_security_to_fibo_equity(
        self, security: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map a Security entity to FIBOEquityInstrument."""
        fibo_entity = FIBOEquityInstrument(
            id=f"fibo-{security['id']}",
            name=security.get("name", "Unknown Equity"),
            fibo_type="EquityInstrument",
            isin=security.get("isin"),
            cusip=security.get("cusip"),
            ticker=security.get("symbol"),
            exchange=security.get("exchange"),
            currency=security.get("currency", "USD"),
            issuer_lei=security.get("issuer_lei"),
            share_class=security.get("share_class", "COMMON"),
        )

        created_entity = await self.neo4j_service.create_entity(
            "FIBOEquityInstrument", fibo_entity.dict()
        )

        await self._create_entity_mapping(
            security["id"], "Security", created_entity["id"], "FIBOEquityInstrument"
        )

        return created_entity

    async def _map_account_to_fibo_account(
        self, account: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map an Account entity to FIBOFinancialAccount."""
        fibo_entity = FIBOFinancialAccount(
            id=f"fibo-{account['id']}",
            name=account.get("name", "Unknown Account"),
            fibo_type="FinancialAccount",
            account_identifier=account.get("account_number"),
            account_type=account.get("account_type", "CUSTODY"),
            currency=account.get("currency", "USD"),
            account_status=account.get("status", "ACTIVE"),
            custodian_identifier=account.get("custodian_id"),
        )

        created_entity = await self.neo4j_service.create_entity(
            "FIBOFinancialAccount", fibo_entity.dict()
        )

        await self._create_entity_mapping(
            account["id"], "Account", created_entity["id"], "FIBOFinancialAccount"
        )

        return created_entity

    async def _map_position_to_fibo_holding(
        self, position: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map a Position entity to FIBOPositionHolding."""
        fibo_entity = FIBOPositionHolding(
            id=f"fibo-{position['id']}",
            name=f"Position {position.get('id', 'Unknown')}",
            fibo_type="PositionHolding",
            account_identifier=position.get("account_id"),
            instrument_identifier=position.get("security_id"),
            quantity=float(position.get("quantity", 0)),
            market_value=float(position.get("market_value", 0)),
            currency=position.get("currency", "USD"),
            valuation_date=position.get("valuation_date"),
            position_type=position.get("position_type", "LONG"),
        )

        created_entity = await self.neo4j_service.create_entity(
            "FIBOPositionHolding", fibo_entity.dict()
        )

        await self._create_entity_mapping(
            position["id"], "Position", created_entity["id"], "FIBOPositionHolding"
        )

        return created_entity

    async def _create_entity_mapping(
        self,
        original_id: str,
        original_type: str,
        fibo_id: str,
        fibo_type: str,
    ) -> None:
        """Create a mapping relationship between original and FIBO entities."""
        mapping = FIBOOntologyMapping(
            id=f"mapping-{original_id}-{fibo_id}",
            name=f"Mapping {original_type} to {fibo_type}",
            original_entity_id=original_id,
            original_entity_type=original_type,
            fibo_entity_id=fibo_id,
            fibo_entity_type=fibo_type,
            mapping_confidence=0.95,
            mapping_status="ACTIVE",
        )

        await self.neo4j_service.create_entity("FIBOOntologyMapping", mapping.dict())

        await self.neo4j_service.create_relationship(
            original_type,
            original_id,
            fibo_type,
            fibo_id,
            "MAPPED_TO_FIBO",
            {"mapping_date": mapping.created_at, "confidence": mapping.mapping_confidence},
        )

    async def query_fibo_entities(
        self, query: FIBOQuery
    ) -> List[Dict[str, Any]]:
        """Query FIBO entities with flexible criteria."""
        try:
            cypher_parts = []
            parameters = {}

            if query.entity_types:
                entity_labels = "|".join(query.entity_types)
                cypher_parts.append(f"MATCH (e:{entity_labels})")
            else:
                cypher_parts.append("MATCH (e)")
                cypher_parts.append("WHERE labels(e)[0] STARTS WITH 'FIBO'")

            if query.property_filters:
                where_conditions = []
                for prop, value in query.property_filters.items():
                    param_name = f"prop_{prop}"
                    where_conditions.append(f"e.{prop} = ${param_name}")
                    parameters[param_name] = value

                if where_conditions:
                    if "WHERE" in " ".join(cypher_parts):
                        cypher_parts.append("AND " + " AND ".join(where_conditions))
                    else:
                        cypher_parts.append("WHERE " + " AND ".join(where_conditions))

            if query.relationship_filters:
                for rel_filter in query.relationship_filters:
                    rel_type = rel_filter.get("type")
                    rel_direction = rel_filter.get("direction", "outgoing")

                    if rel_direction == "outgoing":
                        cypher_parts.append(f"MATCH (e)-[:{rel_type}]->(related)")
                    elif rel_direction == "incoming":
                        cypher_parts.append(f"MATCH (related)-[:{rel_type}]->(e)")
                    else:
                        cypher_parts.append(f"MATCH (e)-[:{rel_type}]-(related)")

            cypher_parts.append("RETURN e")

            if query.limit:
                cypher_parts.append(f"LIMIT {query.limit}")

            cypher_query = " ".join(cypher_parts)
            logger.info(f"Executing FIBO query: {cypher_query}")

            results = await self.neo4j_service.execute_cypher(cypher_query, parameters)
            return [result["e"] for result in results if "e" in result]

        except Exception as e:
            logger.error(f"Failed to query FIBO entities: {e}")
            return []

    async def get_fibo_statistics(self) -> Dict[str, Any]:
        """Get statistics about FIBO entities in the knowledge graph."""
        try:
            stats_queries = {
                "fibo_legal_entities": "MATCH (e:FIBOLegalEntity) RETURN count(e) as count",
                "fibo_financial_accounts": "MATCH (e:FIBOFinancialAccount) RETURN count(e) as count",
                "fibo_equity_instruments": "MATCH (e:FIBOEquityInstrument) RETURN count(e) as count",
                "fibo_position_holdings": "MATCH (e:FIBOPositionHolding) RETURN count(e) as count",
                "fibo_mappings": "MATCH (e:FIBOOntologyMapping) RETURN count(e) as count",
                "fibo_relationships": "MATCH ()-[r]->() WHERE type(r) STARTS WITH 'FIBO_' RETURN count(r) as count",
            }

            statistics = {}
            for stat_name, query in stats_queries.items():
                results = await self.neo4j_service.execute_cypher(query)
                statistics[stat_name] = results[0]["count"] if results else 0

            return statistics

        except Exception as e:
            logger.error(f"Failed to get FIBO statistics: {e}")
            return {}


async def get_fibo_service() -> FIBOService:
    """Dependency injection for FIBO service."""
    neo4j_service = await get_neo4j_service()
    return FIBOService(neo4j_service)
