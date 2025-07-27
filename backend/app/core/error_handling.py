"""
Enhanced error handling for banking operations.
Provides secure error responses that don't leak sensitive information.
"""

import logging
import traceback
from typing import Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Exception for security-related errors."""
    pass


class BankingOperationError(Exception):
    """Exception for banking operation errors."""
    pass


class EnhancedErrorHandler(BaseHTTPMiddleware):
    """Enhanced error handling middleware for banking operations."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException as exc:
            return await self.handle_http_exception(request, exc)
        except SecurityError as exc:
            return await self.handle_security_error(request, exc)
        except BankingOperationError as exc:
            return await self.handle_banking_error(request, exc)
        except Exception as exc:
            return await self.handle_unexpected_error(request, exc)
    
    async def handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions with secure error responses."""
        # Log the error for monitoring
        logger.warning(
            f"HTTP Exception on {request.method} {request.url}: {exc.status_code} - {exc.detail}",
            extra={
                "method": request.method,
                "url": str(request.url),
                "status_code": exc.status_code,
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "type": "http_error",
                    "timestamp": logger.time() if hasattr(logger, 'time') else None
                }
            }
        )
    
    async def handle_security_error(self, request: Request, exc: SecurityError) -> JSONResponse:
        """Handle security-related errors with appropriate logging."""
        # Security errors are always logged as warnings or errors
        logger.error(
            f"Security error on {request.method} {request.url}: {str(exc)}",
            extra={
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else "unknown",
                "error_type": "security_error"
            }
        )
        
        # Return generic error message to not leak security information
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": {
                    "code": 403,
                    "message": "Access denied. Please contact support if this error persists.",
                    "type": "security_error",
                    "reference_id": id(exc)  # Unique reference for support
                }
            }
        )
    
    async def handle_banking_error(self, request: Request, exc: BankingOperationError) -> JSONResponse:
        """Handle banking operation errors with appropriate logging."""
        logger.error(
            f"Banking operation error on {request.method} {request.url}: {str(exc)}",
            extra={
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else "unknown",
                "error_type": "banking_error"
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": 422,
                    "message": "Banking operation failed. Please verify your input and try again.",
                    "type": "banking_error",
                    "details": str(exc)  # Banking errors can show more detail
                }
            }
        )
    
    async def handle_unexpected_error(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected errors with secure logging."""
        # Log full traceback for debugging, but don't expose it
        logger.error(
            f"Unexpected error on {request.method} {request.url}: {str(exc)}",
            extra={
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else "unknown",
                "error_type": "unexpected_error",
                "traceback": traceback.format_exc()
            }
        )
        
        # Return generic error message
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": 500,
                    "message": "An unexpected error occurred. Please try again later.",
                    "type": "internal_error",
                    "reference_id": id(exc)  # Unique reference for support
                }
            }
        )


def create_error_response(
    status_code: int,
    message: str,
    error_type: str = "error",
    details: Dict[str, Any] = None
) -> JSONResponse:
    """Create a standardized error response."""
    content = {
        "error": {
            "code": status_code,
            "message": message,
            "type": error_type
        }
    }
    
    if details:
        content["error"]["details"] = details
    
    return JSONResponse(status_code=status_code, content=content)


def validate_banking_operation(
    operation_type: str,
    amount: float = None,
    currency: str = None,
    customer_id: str = None
):
    """Validate banking operation parameters and raise appropriate errors."""
    if operation_type not in ["deposit", "withdrawal", "transfer", "query"]:
        raise BankingOperationError(f"Invalid operation type: {operation_type}")
    
    if amount is not None:
        if amount <= 0:
            raise BankingOperationError("Amount must be positive")
        
        if amount > 1000000:  # 1 million limit
            raise BankingOperationError("Amount exceeds transaction limit")
    
    if currency and currency not in ["USD", "EUR", "GBP", "JPY", "CHF"]:
        raise BankingOperationError(f"Unsupported currency: {currency}")
    
    if customer_id and not customer_id.startswith("CUST_"):
        raise BankingOperationError("Invalid customer ID format")


# Security-focused logging configuration
def setup_secure_logging():
    """Configure secure logging for banking operations."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            # In production, add secure file handler or external logging service
        ]
    )
    
    # Configure specific loggers for security events
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.WARNING)
    
    banking_logger = logging.getLogger('banking')
    banking_logger.setLevel(logging.INFO)
    
    return {
        'security': security_logger,
        'banking': banking_logger
    }