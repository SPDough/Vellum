#!/usr/bin/env python3
"""
Simple FastAPI server for local development and testing
"""

import json
import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# Simple data models
class DataRecord(BaseModel):
    id: str
    timestamp: datetime
    source: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class FilterRequest(BaseModel):
    filters: Optional[Dict[str, Any]] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"
    page: int = 1
    page_size: int = 50


# Initialize FastAPI app
app = FastAPI(
    title="Otomeshon Simple Backend",
    description="Simplified backend for local testing",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
sample_data: List[DataRecord] = []


def generate_sample_data() -> None:
    """Generate sample data for testing the Data Sandbox"""
    sources = ["workflow", "api", "mcp", "manual"]
    data_types = ["trade", "sop", "analytics", "report"]

    for i in range(100):
        record = DataRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now() - timedelta(hours=random.randint(0, 168)),
            source=random.choice(sources),
            data={
                "type": random.choice(data_types),
                "amount": round(random.uniform(100, 10000), 2),
                "currency": random.choice(["USD", "EUR", "GBP", "JPY"]),
                "status": random.choice(["pending", "completed", "failed"]),
                "customer_id": f"CUST_{random.randint(1000, 9999)}",
                "description": f"Sample transaction {i+1}",
                "risk_score": round(random.uniform(0, 1), 3),
            },
            metadata={
                "created_by": "system",
                "version": "1.0",
                "tags": random.sample(
                    ["high_value", "urgent", "review", "automated"],
                    k=random.randint(1, 2),
                ),
            },
        )
        sample_data.append(record)


# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "otomeshon-simple",
    }


# Data Sandbox API endpoints
@app.get("/api/v1/data-sandbox/records")
async def get_records(
    page: int = 1,
    page_size: int = 50,
    source: Optional[str] = None,
    data_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Get paginated data records with optional filtering"""

    # Filter data
    filtered_data = sample_data
    if source:
        filtered_data = [r for r in filtered_data if r.source == source]
    if data_type:
        filtered_data = [r for r in filtered_data if r.data.get("type") == data_type]

    # Pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_data = filtered_data[start_idx:end_idx]

    return {
        "data": [r.dict() for r in page_data],
        "total": len(filtered_data),
        "page": page,
        "page_size": page_size,
        "total_pages": (len(filtered_data) + page_size - 1) // page_size,
    }


@app.post("/api/v1/data-sandbox/filter")
async def filter_records(request: FilterRequest) -> Dict[str, Any]:
    """Advanced filtering of data records"""

    filtered_data = sample_data

    # Apply filters if provided
    if request.filters:
        for key, value in request.filters.items():
            if key == "source":
                filtered_data = [r for r in filtered_data if r.source == value]
            elif key == "date_from":
                try:
                    date_from = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    filtered_data = [
                        r for r in filtered_data if r.timestamp >= date_from
                    ]
                except:
                    pass
            elif key == "date_to":
                try:
                    date_to = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    filtered_data = [r for r in filtered_data if r.timestamp <= date_to]
                except:
                    pass

    # Sort data
    if request.sort_by:
        reverse = request.sort_order == "desc"
        if request.sort_by == "timestamp":
            filtered_data.sort(key=lambda x: x.timestamp, reverse=reverse)
        elif request.sort_by == "source":
            filtered_data.sort(key=lambda x: x.source, reverse=reverse)

    # Pagination
    start_idx = (request.page - 1) * request.page_size
    end_idx = start_idx + request.page_size
    page_data = filtered_data[start_idx:end_idx]

    return {
        "data": [r.dict() for r in page_data],
        "total": len(filtered_data),
        "page": request.page,
        "page_size": request.page_size,
        "total_pages": (len(filtered_data) + request.page_size - 1)
        // request.page_size,
    }


@app.get("/api/v1/data-sandbox/sources")
async def get_data_sources() -> Dict[str, List[str]]:
    """Get available data sources"""
    sources = list(set(r.source for r in sample_data))
    return {"sources": sources}


@app.get("/api/v1/data-sandbox/stats")
async def get_stats() -> Dict[str, Any]:
    """Get data sandbox statistics"""
    total_records = len(sample_data)
    sources_count: Dict[str, int] = {}
    for record in sample_data:
        sources_count[record.source] = sources_count.get(record.source, 0) + 1

    return {
        "total_records": total_records,
        "sources": sources_count,
        "last_updated": max(r.timestamp for r in sample_data) if sample_data else None,
    }


@app.post("/api/v1/data-sandbox/export")
async def export_data(request: Dict[str, Any]) -> Dict[str, Any]:
    """Export data in various formats"""

    return {
        "export_id": str(uuid.uuid4()),
        "format": request.get("format", "csv"),
        "status": "processing",
        "download_url": f"/api/v1/data-sandbox/download/{uuid.uuid4()}",
        "created_at": datetime.now(),
    }


# WebSocket stats endpoint (simplified)
@app.get("/api/v1/data-sandbox/ws/stats")
async def websocket_stats() -> Dict[str, Any]:
    """Get WebSocket connection stats for monitoring"""
    return {
        "active_connections": random.randint(1, 10),
        "messages_sent": random.randint(100, 1000),
        "last_activity": datetime.now(),
    }


# Metrics endpoint for monitoring
@app.get("/metrics")
async def metrics() -> Dict[str, Any]:
    """Prometheus-style metrics endpoint"""
    return {
        "otomeshon_websocket_connections_total": random.randint(1, 10),
        "otomeshon_data_sandbox_records_total": len(sample_data),
        "otomeshon_data_exports_total": random.randint(50, 200),
    }


# Initialize sample data on startup
@app.on_event("startup")
async def startup_event() -> None:
    """Initialize the application with sample data"""
    generate_sample_data()
    print(f"🎯 Generated {len(sample_data)} sample records")
    print("🚀 Simple Otomeshon Backend is ready!")
    print("📊 Data Sandbox API available at /api/v1/data-sandbox/")
    print("📖 API Documentation available at /docs")


def custom_openapi() -> Dict[str, Any]:
    """Custom OpenAPI schema."""
    if app.openapi_schema:
        return dict(app.openapi_schema)

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title="Otomeshon Simple Backend",
        version="1.0.0",
        description="Simplified backend for local testing",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return dict(openapi_schema)


app.openapi = custom_openapi


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Application shutdown event."""
    logger = logging.getLogger(__name__)
    logger.info("🛑 Vellum API shutting down...")


if __name__ == "__main__":
    uvicorn.run(
        "main_simple:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
