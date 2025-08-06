import asyncio
from contextlib import asynccontextmanager


from typing import AsyncGenerator, Generator, Optional

import psycopg
from neo4j import AsyncDriver, AsyncGraphDatabase, GraphDatabase
from sqlalchemy import create_engine, text

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.base import Base as DataSandboxBase
from app.core.config import get_settings
from app.models.sop import Base as SOPBase
from app.models.trade import Base as TradeBase
from app.models.workflow import Base as WorkflowBase

settings = get_settings()

# PostgreSQL setup
engine = create_async_engine(
    settings.database_url,
    echo=True if settings.log_level == "DEBUG" else False,
    pool_pre_ping=True,
    pool_recycle=300,
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Sync engine for Alembic migrations
sync_engine = create_engine(
    settings.database_url.replace("postgresql://", "postgresql+psycopg://"),
    echo=True if settings.log_level == "DEBUG" else False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self) -> None:
        self.neo4j_driver: Optional[AsyncDriver] = None
        self.postgres_engine = engine

    async def init_postgres(self) -> None:
        """Initialize PostgreSQL database and tables."""
        try:
            # Create all tables
            async with engine.begin() as conn:
                # Enable pgvector extension
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

                # Create all tables from all Base classes
                await conn.run_sync(TradeBase.metadata.create_all)
                await conn.run_sync(SOPBase.metadata.create_all)
                await conn.run_sync(WorkflowBase.metadata.create_all)

            print("✅ PostgreSQL initialized successfully")

        except Exception as e:
            print(f"❌ Failed to initialize PostgreSQL: {e}")
            raise

    async def init_neo4j(self) -> None:
        """Initialize Neo4j connection and constraints."""
        try:
            self.neo4j_driver = AsyncGraphDatabase.driver(
                settings.neo4j_url, auth=(settings.neo4j_user, settings.neo4j_password)
            )

            # Test connection
            if self.neo4j_driver:
                await self.neo4j_driver.verify_connectivity()

                # Create constraints and indexes
                async with self.neo4j_driver.session() as session:
                    # SOP Document constraints
                    await session.run(
                        """
                    CREATE CONSTRAINT sop_document_id IF NOT EXISTS
                    FOR (s:SOPDocument) REQUIRE s.id IS UNIQUE
                """
                    )

                await session.run(
                    """
                    CREATE CONSTRAINT sop_document_number IF NOT EXISTS
                    FOR (s:SOPDocument) REQUIRE s.document_number IS UNIQUE
                """
                )

                # SOP Step constraints
                await session.run(
                    """
                    CREATE CONSTRAINT sop_step_id IF NOT EXISTS
                    FOR (s:SOPStep) REQUIRE s.id IS UNIQUE
                """
                )

                # Process constraints
                await session.run(
                    """
                    CREATE CONSTRAINT process_id IF NOT EXISTS
                    FOR (p:Process) REQUIRE p.id IS UNIQUE
                """
                )

                # Trade constraints
                await session.run(
                    """
                    CREATE CONSTRAINT trade_id IF NOT EXISTS
                    FOR (t:Trade) REQUIRE t.id IS UNIQUE
                """
                )

                # Create vector index for semantic search
                await session.run(
                    """
                    CREATE VECTOR INDEX sop_embeddings IF NOT EXISTS
                    FOR (s:SOPDocument) ON (s.embeddings)
                    OPTIONS {indexConfig: {
                        `vector.dimensions`: 1536,
                        `vector.similarity_function`: 'cosine'
                    }}
                """
                )

                # Create text indexes for full-text search
                await session.run(
                    """
                    CREATE FULLTEXT INDEX sop_content_fulltext IF NOT EXISTS
                    FOR (s:SOPDocument) ON EACH [s.title, s.content, s.summary]
                """
                )

            print("✅ Neo4j initialized successfully")

        except Exception as e:
            print(f"❌ Failed to initialize Neo4j: {e}")
            raise

    async def close_connections(self) -> None:
        """Close all database connections."""
        if self.neo4j_driver:
            await self.neo4j_driver.close()
        await engine.dispose()


# Global database manager instance
db_manager = DatabaseManager()


Base = TradeBase

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session (alias for get_db)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Dependency for getting async database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Dependency for getting sync database session
def get_sync_db() -> Generator[Session, None, None]:
    """Get sync database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependency for getting Neo4j session
@asynccontextmanager
async def get_neo4j_session() -> AsyncGenerator:
    """Get Neo4j async session."""
    if not db_manager.neo4j_driver:
        raise RuntimeError("Neo4j driver not initialized")

    async with db_manager.neo4j_driver.session() as session:
        yield session


# Database initialization function
async def init_db() -> None:
    """Initialize all databases."""
    await db_manager.init_postgres()
    await db_manager.init_neo4j()


# Database cleanup function
async def close_db() -> None:
    """Close all database connections."""
    await db_manager.close_connections()


class Neo4jService:
    """Service for Neo4j operations."""

    @staticmethod
    async def create_sop_document(sop_data: dict) -> str:
        """Create SOP document in Neo4j knowledge graph."""
        async with get_neo4j_session() as session:
            result = await session.run(
                """
                CREATE (s:SOPDocument {
                    id: $id,
                    title: $title,
                    document_number: $document_number,
                    version: $version,
                    content: $content,
                    summary: $summary,
                    category: $category,
                    subcategory: $subcategory,
                    process_type: $process_type,
                    business_area: $business_area,
                    created_at: datetime(),
                    embeddings: $embeddings
                })
                RETURN s.id as id
            """,
                **sop_data,
            )

            record = await result.single()

            return str(record["id"]) if record else ""

    @staticmethod
    async def create_sop_relationships(sop_id: str, relationships: list) -> None:
        """Create relationships between SOP documents."""
        async with get_neo4j_session() as session:
            for rel in relationships:
                await session.run(
                    """
                    MATCH (s1:SOPDocument {id: $source_id})
                    MATCH (s2:SOPDocument {id: $target_id})
                    CREATE (s1)-[r:%s {
                        type: $rel_type,
                        confidence: $confidence,
                        created_at: datetime()
                    }]->(s2)
                """
                    % rel["relationship_type"],
                    {
                        "source_id": sop_id,
                        "target_id": rel["target_id"],
                        "rel_type": rel["type"],
                        "confidence": rel.get("confidence", 1.0),
                    },
                )

    @staticmethod
    async def semantic_search_sops(query_embedding: list, limit: int = 10) -> list:
        """Perform semantic search on SOP documents."""
        async with get_neo4j_session() as session:
            result = await session.run(
                """
                CALL db.index.vector.queryNodes('sop_embeddings', $limit, $query_embedding)
                YIELD node, score
                RETURN node.id as id,
                       node.title as title,
                       node.category as category,
                       node.business_area as business_area,
                       node.summary as summary,
                       score
                ORDER BY score DESC
            """,
                {"query_embedding": query_embedding, "limit": limit},
            )

            return [dict(record) async for record in result]

    @staticmethod
    async def get_related_sops(
        sop_id: str, relationship_types: Optional[list] = None
    ) -> list:
        """Get SOPs related to a given SOP."""
        rel_filter = ""
        if relationship_types:
            rel_filter = f"WHERE type(r) IN {relationship_types}"

        async with get_neo4j_session() as session:
            result = await session.run(
                f"""
                MATCH (s1:SOPDocument {{id: $sop_id}})-[r]->(s2:SOPDocument)
                {rel_filter}
                RETURN s2.id as id,
                       s2.title as title,
                       s2.category as category,
                       type(r) as relationship_type,
                       r.confidence as confidence
                ORDER BY r.confidence DESC
            """,
                {"sop_id": sop_id},
            )

            return [dict(record) async for record in result]
