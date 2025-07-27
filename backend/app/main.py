import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.telemetry import setup_telemetry
from app.services.kafka_service import kafka_service
from app.services.knowledge_graph_sync_service import kg_sync_service
from app.services.neo4j_service import neo4j_service
from app.services.temporal_service import temporal_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    settings = get_settings()

    # Setup telemetry
    setup_telemetry(settings)

    # Initialize database
    await init_db()

    # Initialize Neo4j knowledge graph
    await neo4j_service.connect()

    # Initialize knowledge graph sync service
    await kg_sync_service.initialize()

    # Sync initial data to knowledge graph
    await kg_sync_service.sync_all_data()

    # Start background services
    await kafka_service.start()
    await temporal_service.start()

    yield

    # Cleanup
    await kafka_service.stop()
    await temporal_service.stop()
    await neo4j_service.disconnect()


app = FastAPI(
    title="Otomeshon",
    description="Agentic trading system with LangGraph workflows and knowledge graphs",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Security
security = HTTPBearer()


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "otomeshon-api", "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Otomeshon API", "docs": "/docs", "health": "/health"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
