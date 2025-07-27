#!/usr/bin/env python3
"""
Simple FastAPI server for local development and testing
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import uvicorn
import os

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

# Simple authentication models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: Dict[str, Any]

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    role: str
    department: Optional[str] = None

class AuthConfigResponse(BaseModel):
    current_provider: str
    available_providers: List[str]
    keycloak_available: bool
    endpoints: Dict[str, str]

# Initialize FastAPI app
app = FastAPI(
    title="Otomeshon Simple Backend",
    description="Simplified backend for local testing",
    version="1.0.0"
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

# Simple in-memory user storage for demo
demo_users = {
    "admin@otomeshon.ai": {
        "id": 1,
        "email": "admin@otomeshon.ai", 
        "username": "admin",
        "password": "admin123",  # In production, this would be hashed
        "full_name": "System Administrator",
        "role": "admin",
        "department": "IT"
    },
    "analyst@otomeshon.ai": {
        "id": 2,
        "email": "analyst@otomeshon.ai",
        "username": "analyst", 
        "password": "analyst123",
        "full_name": "Data Analyst",
        "role": "analyst",
        "department": "Analytics"
    }
}

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
                "risk_score": round(random.uniform(0, 1), 3)
            },
            metadata={
                "created_by": "system",
                "version": "1.0",
                "tags": random.sample(["high_value", "urgent", "review", "automated"], k=random.randint(1, 2))
            }
        )
        sample_data.append(record)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Otomeshon.ai Banking Platform API", 
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "auth": "/api/auth/*",
            "data_sandbox": "/api/v1/data-sandbox/*"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(), "service": "otomeshon-simple"}

# Simple Authentication endpoints
@app.post("/api/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Simple authentication for demo purposes"""
    
    user = demo_users.get(login_data.email)
    if not user or user["password"] != login_data.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Generate simple tokens (in production, use proper JWT)
    access_token = f"access_{uuid.uuid4()}"
    refresh_token = f"refresh_{uuid.uuid4()}"
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=3600,
        user={
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "department": user["department"]
        }
    )

@app.post("/api/auth/logout")
async def logout():
    """Simple logout endpoint"""
    return {"message": "Successfully logged out"}

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user():
    """Get current user info - simplified for demo"""
    # In a real app, you'd extract user from JWT token
    # For demo, return admin user
    user = demo_users["admin@otomeshon.ai"]
    return UserResponse(
        id=user["id"],
        email=user["email"],
        username=user["username"],
        full_name=user["full_name"],
        role=user["role"],
        department=user["department"]
    )

@app.get("/api/auth/config", response_model=AuthConfigResponse)
async def get_auth_config():
    """Get authentication configuration"""
    
    # Check if running in Docker (Keycloak available)
    auth_provider = os.getenv("AUTH_PROVIDER", "simple")
    keycloak_available = os.getenv("KEYCLOAK_URL") is not None
    
    return AuthConfigResponse(
        current_provider=auth_provider,
        available_providers=["simple", "keycloak"],
        keycloak_available=keycloak_available,
        endpoints={
            "login": "/api/auth/login",
            "logout": "/api/auth/logout", 
            "me": "/api/auth/me",
            "config": "/api/auth/config"
        }
    )

@app.get("/api/auth/providers")
async def get_auth_providers():
    """Get available authentication providers"""
    
    auth_provider = os.getenv("AUTH_PROVIDER", "simple")
    keycloak_available = os.getenv("KEYCLOAK_URL") is not None
    
    return {
        "providers": ["simple", "keycloak"],
        "current": auth_provider,
        "keycloak_available": keycloak_available,
        "simple": {
            "name": "Simple JWT Authentication",
            "description": "Basic email/password with JWT tokens",
            "demo_accounts": [
                {"email": "admin@otomeshon.ai", "password": "admin123", "role": "admin"},
                {"email": "analyst@otomeshon.ai", "password": "analyst123", "role": "analyst"}
            ]
        },
        "keycloak": {
            "name": "Keycloak OIDC",
            "description": "Enterprise authentication via Keycloak",
            "available": keycloak_available,
            "realm_url": os.getenv("KEYCLOAK_URL", "http://localhost:8080") + "/realms/oto",
            "client_id": "Otomeshon-CustodianPortal",
            "demo_accounts": [
                {"email": "admin@otomeshon.ai", "password": "admin123", "role": "admin"},
                {"email": "manager@otomeshon.ai", "password": "manager123", "role": "manager"},
                {"email": "analyst@otomeshon.ai", "password": "analyst123", "role": "analyst"}
            ]
        }
    }

# Data Sandbox API endpoints
@app.get("/api/v1/data-sandbox/records")
async def get_records(
    page: int = 1,
    page_size: int = 50,
    source: Optional[str] = None,
    data_type: Optional[str] = None
):
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
        "total_pages": (len(filtered_data) + page_size - 1) // page_size
    }

@app.post("/api/v1/data-sandbox/filter")
async def filter_records(request: FilterRequest):
    """Advanced filtering of data records"""
    
    filtered_data = sample_data
    
    # Apply filters if provided
    if request.filters:
        for key, value in request.filters.items():
            if key == "source":
                filtered_data = [r for r in filtered_data if r.source == value]
            elif key == "date_from":
                try:
                    date_from = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    filtered_data = [r for r in filtered_data if r.timestamp >= date_from]
                except:
                    pass
            elif key == "date_to":
                try:
                    date_to = datetime.fromisoformat(value.replace('Z', '+00:00'))
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
        "total_pages": (len(filtered_data) + request.page_size - 1) // request.page_size
    }

@app.get("/api/v1/data-sandbox/sources")
async def get_data_sources():
    """Get available data sources"""
    sources = list(set(r.source for r in sample_data))
    return {"sources": sources}

@app.get("/api/v1/data-sandbox/stats")
async def get_stats():
    """Get data sandbox statistics"""
    total_records = len(sample_data)
    sources_count = {}
    for record in sample_data:
        sources_count[record.source] = sources_count.get(record.source, 0) + 1
    
    return {
        "total_records": total_records,
        "sources": sources_count,
        "last_updated": max(r.timestamp for r in sample_data) if sample_data else None
    }

@app.post("/api/v1/data-sandbox/export")
async def export_data(request: Dict[str, Any]):
    """Export data in various formats"""
    
    return {
        "export_id": str(uuid.uuid4()),
        "format": request.get("format", "csv"),
        "status": "processing",
        "download_url": f"/api/v1/data-sandbox/download/{uuid.uuid4()}",
        "created_at": datetime.now()
    }

# WebSocket stats endpoint (simplified)
@app.get("/api/v1/data-sandbox/ws/stats")
async def websocket_stats():
    """Get WebSocket connection stats for monitoring"""
    return {
        "active_connections": random.randint(1, 10),
        "messages_sent": random.randint(100, 1000),
        "last_activity": datetime.now()
    }

# Metrics endpoint for monitoring
@app.get("/metrics")
async def metrics():
    """Prometheus-style metrics endpoint"""
    return {
        "otomeshon_websocket_connections_total": random.randint(1, 10),
        "otomeshon_data_sandbox_records_total": len(sample_data),
        "otomeshon_data_exports_total": random.randint(50, 200)
    }

# Initialize sample data on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the application with sample data"""
    generate_sample_data()
    print(f"🎯 Generated {len(sample_data)} sample records")
    print("🚀 Simple Otomeshon Backend is ready!")
    print("📊 Data Sandbox API available at /api/v1/data-sandbox/")
    print("📖 API Documentation available at /docs")

if __name__ == "__main__":
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )