import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.middleware import (
    ErrorHandlingMiddleware,
    RateLimitingMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
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
    description="Middle office automations and back office validations for custodian banks — AI-powered workflows, NAV validation, and data sandbox.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add middleware in correct order (last added = first executed)
# 1. Error handling (catch all errors)
app.add_middleware(ErrorHandlingMiddleware)

# 2. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. Request logging and rate limiting
settings = get_settings()
if settings.environment == "production":
    app.add_middleware(RateLimitingMiddleware, requests_per_minute=100)

app.add_middleware(
    RequestLoggingMiddleware,
    log_requests=True,
    log_responses=settings.environment == "development",
)

# 4. CORS (should be last)
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


def custom_openapi() -> Dict[str, Any]:
    """Custom OpenAPI schema."""
    if app.openapi_schema:
        return dict(app.openapi_schema)

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title="Otomeshon",
        version="1.0.0",
        description="Middle office automations and back office validations for custodian banks — AI-powered workflows, NAV validation, and data sandbox.",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return dict(openapi_schema)


app.openapi = custom_openapi


@app.on_event("startup")
async def startup_event() -> None:
    """Application startup event."""
    pass


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "otomeshon-api", "version": "1.0.0"}


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {"message": "Otomeshon API", "docs": "/docs", "health": "/health"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
