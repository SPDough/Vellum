"""
Middleware for error handling, authentication, and request processing
"""

import json
import time
import traceback
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

import structlog
from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = structlog.get_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global error handling middleware for consistent error responses
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid4())
        request.state.request_id = request_id

        try:
            # Add request timing
            start_time = time.time()

            # Process the request
            response = await call_next(request)

            # Add timing header
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id

            return response

        except HTTPException as http_exc:
            # FastAPI HTTPExceptions - preserve them
            return JSONResponse(
                status_code=http_exc.status_code,
                content={
                    "error": {
                        "code": http_exc.status_code,
                        "message": http_exc.detail,
                        "type": "http_exception",
                        "request_id": request_id,
                    }
                },
                headers=http_exc.headers,
            )

        except ValidationError as validation_exc:
            # Pydantic validation errors
            logger.error(
                "Validation error",
                request_id=request_id,
                path=request.url.path,
                errors=validation_exc.errors(),
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": {
                        "code": 422,
                        "message": "Validation failed",
                        "type": "validation_error",
                        "details": validation_exc.errors(),
                        "request_id": request_id,
                    }
                },
            )

        except Exception as exc:
            # Catch-all for unexpected errors
            logger.error(
                "Unhandled exception",
                request_id=request_id,
                path=request.url.path,
                method=request.method,
                exception=str(exc),
                traceback=traceback.format_exc(),
            )

            # In development, include more details
            error_detail = {
                "code": 500,
                "message": "Internal server error",
                "type": "internal_error",
                "request_id": request_id,
            }

            # Add debug info in development
            try:
                from app.core.config import get_settings

                settings = get_settings()
                if settings.environment == "development":
                    error_detail["debug"] = {
                        "exception": str(exc),
                        "traceback": traceback.format_exc().split("\n"),
                    }
            except:
                pass  # Fail silently if config unavailable

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": error_detail},
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Remove server header for security
        if "server" in response.headers:
            del response.headers["server"]

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log incoming requests and responses for audit purposes
    """

    def __init__(
        self,
        app,
        *,
        log_requests: bool = True,
        log_responses: bool = False,
        log_request_body: bool = False,
        log_response_body: bool = False,
        exclude_paths: Optional[set] = None,
    ):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.exclude_paths = exclude_paths or {
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
        }

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        request_id = getattr(request.state, "request_id", str(uuid4()))
        start_time = time.time()

        # Log request
        if self.log_requests:
            request_data = {
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "content_type": request.headers.get("content-type"),
                "content_length": request.headers.get("content-length"),
            }

            # Log request body if enabled (be careful with sensitive data)
            if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    if body:
                        # Only log non-binary content
                        if request.headers.get("content-type", "").startswith(
                            "application/json"
                        ):
                            request_data["body"] = json.loads(body.decode())
                        else:
                            request_data["body_size"] = len(body)
                except Exception:
                    request_data["body"] = "Failed to read body"

            logger.info("Incoming request", **request_data)

        # Process request
        response = await call_next(request)

        # Log response
        if self.log_responses:
            process_time = time.time() - start_time
            response_data = {
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": round(process_time, 3),
                "response_size": response.headers.get("content-length"),
            }

            logger.info("Request completed", **response_data)

        return response


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware (in-memory, not distributed)
    For production, use Redis-based rate limiting
    """

    def __init__(
        self,
        app,
        *,
        requests_per_minute: int = 60,
        burst_limit: int = 100,
        exclude_paths: Optional[set] = None,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.exclude_paths = exclude_paths or {"/health", "/metrics"}
        self.request_counts: Dict[str, Dict[str, Any]] = {}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Clean old entries (older than 1 minute)
        cutoff_time = current_time - 60
        self.request_counts = {
            ip: data
            for ip, data in self.request_counts.items()
            if data["last_request"] > cutoff_time
        }

        # Initialize or update client data
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {
                "count": 0,
                "last_request": current_time,
                "window_start": current_time,
            }

        client_data = self.request_counts[client_ip]

        # Reset window if it's been more than a minute
        if current_time - client_data["window_start"] >= 60:
            client_data["count"] = 0
            client_data["window_start"] = current_time

        # Check rate limit
        client_data["count"] += 1
        client_data["last_request"] = current_time

        if client_data["count"] > self.requests_per_minute:
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                request_count=client_data["count"],
                path=request.url.path,
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": 429,
                        "message": "Too many requests",
                        "type": "rate_limit_exceeded",
                        "retry_after": 60,
                    }
                },
                headers={"Retry-After": "60"},
            )

        return await call_next(request)


# Import ValidationError here to avoid circular imports
try:
    from pydantic import ValidationError
except ImportError:
    # Fallback for older pydantic versions
    from pydantic.error_wrappers import ValidationError
