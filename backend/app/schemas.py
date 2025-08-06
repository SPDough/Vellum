"""
Shared Pydantic schemas for API responses and requests.
This module contains common data models to eliminate duplication across endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserResponse(BaseModel):
    """Standard user response schema used across API endpoints."""
    id: int
    email: str
    username: str
    full_name: str
    role: str
    department: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    auth_provider: Optional[str] = None
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    detail: str
    error_code: str = "INTERNAL_ERROR"


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    active_connections: int
    messages_sent: int
    last_activity: str