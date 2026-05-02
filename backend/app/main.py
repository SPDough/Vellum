"""
Canonical full backend entrypoint for Vellum.

First-pass cleanup note:
- this is the intended real backend application
- the primary API contract is mounted under `/api/v1/...`
- `app/main_simple.py` remains available for demo/dev-only usage
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.placeholder_auth import PlaceholderAuthMiddleware
from app.core.middleware import (
    ErrorHandlingMiddleware,
    RateLimitingMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.telemetry import setup_telemetry
from app.integrations.bootstrap import register_default_providers
from app.services.kafka_service import kafka_service
from app.services.knowledge_graph_sync_service import kg_sync_service
from app.services.neo4j_service import neo4j_service
from app.services.temporal_service import temporal_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    settings = get_settings()

    # Setup telemetry
    setup_telemetry(settings)

    # Register generalized integration providers.
    register_default_providers()

    try:
        await init_db()
    except Exception as exc:
        logger.exception("Database initialization failed")
        if settings.environment == "production":
            raise
        logger.warning("Continuing startup without full database init: %s", exc)

    if settings.startup_enable_neo4j:
        try:
            await neo4j_service.connect()
        except Exception as exc:
            logger.exception("Neo4j connect failed")
            if settings.environment == "production":
                raise
            logger.warning("Continuing without Neo4j: %s", exc)
    else:
        logger.info("Neo4j startup disabled (STARTUP_ENABLE_NEO4J=false)")

    if settings.startup_enable_kg_sync and settings.startup_enable_neo4j:
        try:
            await kg_sync_service.initialize()
            await kg_sync_service.sync_all_data()
        except Exception as exc:
            logger.exception("Knowledge graph sync failed")
            if settings.environment == "production":
                raise
            logger.warning("Continuing without KG sync: %s", exc)

    if settings.startup_enable_kafka:
        try:
            await kafka_service.start()
        except Exception as exc:
            logger.exception("Kafka start failed")
            if settings.environment == "production":
                raise
            logger.warning("Continuing without Kafka: %s", exc)

    if settings.startup_enable_temporal:
        try:
            await temporal_service.start()
        except Exception as exc:
            logger.exception("Temporal start failed")
            if settings.environment == "production":
                raise
            logger.warning("Continuing without Temporal: %s", exc)

    yield

    if settings.startup_enable_temporal:
        try:
            await temporal_service.stop()
        except Exception as exc:
            logger.warning("Temporal stop: %s", exc)
    if settings.startup_enable_kafka:
        try:
            await kafka_service.stop()
        except Exception as exc:
            logger.warning("Kafka stop: %s", exc)
    if settings.startup_enable_neo4j:
        try:
            await neo4j_service.disconnect()
        except Exception as exc:
            logger.warning("Neo4j disconnect: %s", exc)


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

# 4. CORS (outer stack: add before placeholder so CORS wraps inner app)
_cors_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_settings.cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Placeholder auth (runs innermost / closest to routes; sets request.state.auth_subject)
app.add_middleware(PlaceholderAuthMiddleware)

# Include canonical API routes.
#
# First-pass cleanup rule: the full backend contract is exposed under
# `/api/v1/...`.
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
