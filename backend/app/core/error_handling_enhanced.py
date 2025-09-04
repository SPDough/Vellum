"""
Enhanced Error Handling System for Otomeshon Banking Platform

This module provides comprehensive error handling with:
1. Structured error logging
2. Performance monitoring
3. Automatic recovery mechanisms
4. Banking-specific error handling
5. Audit trail integration
"""

import asyncio
import functools
import inspect
import json
import traceback
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union

import structlog
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.performance import performance_monitor

logger = structlog.get_logger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for banking operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for banking operations."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    DATABASE = "database"
    NETWORK = "network"
    BUSINESS_LOGIC = "business_logic"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    SECURITY = "security"
    SYSTEM = "system"


class BankingException(Exception):
    """Base exception for banking operations with enhanced context."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.BUSINESS_LOGIC,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        retryable: bool = False,
    ):
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.category = category
        self.details = details or {}
        self.user_id = user_id
        self.transaction_id = transaction_id
        self.retryable = retryable
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/API responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "details": self.details,
            "user_id": self.user_id,
            "transaction_id": self.transaction_id,
            "retryable": self.retryable,
            "timestamp": self.timestamp.isoformat(),
        }


class ErrorHandler:
    """Centralized error handling with banking-specific logic."""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.recovery_strategies: Dict[str, Callable] = {}
        self.alert_thresholds: Dict[ErrorSeverity, int] = {
            ErrorSeverity.LOW: 100,
            ErrorSeverity.MEDIUM: 50,
            ErrorSeverity.HIGH: 10,
            ErrorSeverity.CRITICAL: 1,
        }

    def handle_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
    ) -> BankingException:
        """Handle any exception and convert to BankingException."""
        
        # Convert common exceptions to BankingException
        if isinstance(exception, BankingException):
            banking_exception = exception
        elif isinstance(exception, HTTPException):
            banking_exception = BankingException(
                message=exception.detail,
                error_code=f"HTTP_{exception.status_code}",
                severity=ErrorSeverity.MEDIUM if exception.status_code < 500 else ErrorSeverity.HIGH,
                category=ErrorCategory.BUSINESS_LOGIC,
                details={"status_code": exception.status_code},
                user_id=user_id,
                transaction_id=transaction_id,
            )
        elif isinstance(exception, SQLAlchemyError):
            banking_exception = BankingException(
                message="Database operation failed",
                error_code="DATABASE_ERROR",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.DATABASE,
                details={"original_error": str(exception)},
                user_id=user_id,
                transaction_id=transaction_id,
                retryable=True,
            )
        elif isinstance(exception, ValueError):
            banking_exception = BankingException(
                message="Invalid input data",
                error_code="VALIDATION_ERROR",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION,
                details={"original_error": str(exception)},
                user_id=user_id,
                transaction_id=transaction_id,
            )
        elif isinstance(exception, TimeoutError):
            banking_exception = BankingException(
                message="Operation timed out",
                error_code="TIMEOUT_ERROR",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.PERFORMANCE,
                details={"original_error": str(exception)},
                user_id=user_id,
                transaction_id=transaction_id,
                retryable=True,
            )
        else:
            banking_exception = BankingException(
                message="An unexpected error occurred",
                error_code="UNEXPECTED_ERROR",
                severity=ErrorSeverity.CRITICAL,
                category=ErrorCategory.SYSTEM,
                details={
                    "original_error": str(exception),
                    "exception_type": type(exception).__name__,
                },
                user_id=user_id,
                transaction_id=transaction_id,
            )

        # Log the error
        self._log_error(banking_exception, context)
        
        # Update error counts
        self._update_error_counts(banking_exception)
        
        # Check for alerts
        self._check_alerts(banking_exception)
        
        # Attempt recovery if applicable
        if banking_exception.retryable:
            self._attempt_recovery(banking_exception)

        return banking_exception

    def _log_error(self, exception: BankingException, context: Optional[Dict[str, Any]] = None):
        """Log error with structured information."""
        log_data = exception.to_dict()
        if context:
            log_data["context"] = context

        if exception.severity == ErrorSeverity.CRITICAL:
            logger.error("Critical error occurred", **log_data, exc_info=True)
        elif exception.severity == ErrorSeverity.HIGH:
            logger.error("High severity error", **log_data)
        elif exception.severity == ErrorSeverity.MEDIUM:
            logger.warning("Medium severity error", **log_data)
        else:
            logger.info("Low severity error", **log_data)

    def _update_error_counts(self, exception: BankingException):
        """Update error count tracking."""
        key = f"{exception.error_code}_{exception.severity.value}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1

    def _check_alerts(self, exception: BankingException):
        """Check if alert thresholds have been exceeded."""
        threshold = self.alert_thresholds.get(exception.severity, 0)
        key = f"{exception.error_code}_{exception.severity.value}"
        count = self.error_counts.get(key, 0)

        if count >= threshold:
            logger.critical(
                "Error alert threshold exceeded",
                error_code=exception.error_code,
                severity=exception.severity.value,
                count=count,
                threshold=threshold,
            )

    def _attempt_recovery(self, exception: BankingException):
        """Attempt automatic recovery for retryable errors."""
        recovery_strategy = self.recovery_strategies.get(exception.error_code)
        if recovery_strategy:
            try:
                recovery_strategy(exception)
                logger.info("Recovery strategy executed", error_code=exception.error_code)
            except Exception as recovery_error:
                logger.error(
                    "Recovery strategy failed",
                    error_code=exception.error_code,
                    recovery_error=str(recovery_error),
                )

    def register_recovery_strategy(self, error_code: str, strategy: Callable):
        """Register a recovery strategy for a specific error code."""
        self.recovery_strategies[error_code] = strategy

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        return {
            "error_counts": self.error_counts,
            "total_errors": sum(self.error_counts.values()),
            "errors_by_severity": {
                severity.value: sum(
                    count for key, count in self.error_counts.items()
                    if key.endswith(f"_{severity.value}")
                )
                for severity in ErrorSeverity
            },
        }


# Global error handler instance
error_handler = ErrorHandler()


def handle_errors(
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.BUSINESS_LOGIC,
    retryable: bool = False,
):
    """Decorator for automatic error handling."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Extract context from function call
                context = {
                    "function": func.__name__,
                    "module": func.__module__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                }
                
                # Extract user_id and transaction_id from kwargs if available
                user_id = kwargs.get("user_id")
                transaction_id = kwargs.get("transaction_id")
                
                banking_exception = error_handler.handle_exception(
                    e, context, user_id, transaction_id
                )
                
                # Override default values with decorator parameters
                banking_exception.severity = severity
                banking_exception.category = category
                banking_exception.retryable = retryable
                
                raise banking_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Extract context from function call
                context = {
                    "function": func.__name__,
                    "module": func.__module__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                }
                
                # Extract user_id and transaction_id from kwargs if available
                user_id = kwargs.get("user_id")
                transaction_id = kwargs.get("transaction_id")
                
                banking_exception = error_handler.handle_exception(
                    e, context, user_id, transaction_id
                )
                
                # Override default values with decorator parameters
                banking_exception.severity = severity
                banking_exception.category = category
                banking_exception.retryable = retryable
                
                raise banking_exception

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


class EnhancedErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Enhanced error handling middleware for FastAPI."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.utcnow()
        
        try:
            response = await call_next(request)
            
            # Log successful requests for monitoring
            duration = (datetime.utcnow() - start_time).total_seconds()
            performance_monitor.record_response_time(
                f"{request.method}_{request.url.path}",
                duration * 1000
            )
            
            return response
            
        except Exception as e:
            # Extract user information from request
            user_id = None
            transaction_id = None
            
            # Try to get user ID from headers or query params
            if "X-User-ID" in request.headers:
                user_id = request.headers["X-User-ID"]
            elif "user_id" in request.query_params:
                user_id = request.query_params["user_id"]
            
            # Try to get transaction ID
            if "X-Transaction-ID" in request.headers:
                transaction_id = request.headers["X-Transaction-ID"]
            elif "transaction_id" in request.query_params:
                transaction_id = request.query_params["transaction_id"]
            
            # Handle the exception
            banking_exception = error_handler.handle_exception(
                e,
                context={
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers),
                    "client_ip": request.client.host if request.client else None,
                },
                user_id=user_id,
                transaction_id=transaction_id,
            )
            
            # Return structured error response
            return JSONResponse(
                status_code=self._get_http_status_code(banking_exception),
                content={
                    "error": banking_exception.to_dict(),
                    "request_id": transaction_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

    def _get_http_status_code(self, exception: BankingException) -> int:
        """Map BankingException to appropriate HTTP status code."""
        if exception.category == ErrorCategory.AUTHENTICATION:
            return 401
        elif exception.category == ErrorCategory.AUTHORIZATION:
            return 403
        elif exception.category == ErrorCategory.VALIDATION:
            return 400
        elif exception.category == ErrorCategory.DATABASE:
            return 503 if exception.retryable else 500
        elif exception.category == ErrorCategory.NETWORK:
            return 503
        elif exception.category == ErrorCategory.COMPLIANCE:
            return 422
        elif exception.category == ErrorCategory.SECURITY:
            return 403
        else:
            return 500 if exception.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else 400


class BankingErrorRecovery:
    """Banking-specific error recovery strategies."""
    
    @staticmethod
    def database_connection_recovery(exception: BankingException):
        """Recovery strategy for database connection errors."""
        logger.info("Attempting database connection recovery")
        # Implement connection pool refresh, retry logic, etc.
        
    @staticmethod
    def authentication_token_refresh(exception: BankingException):
        """Recovery strategy for authentication token errors."""
        logger.info("Attempting authentication token refresh")
        # Implement token refresh logic
        
    @staticmethod
    def rate_limit_backoff(exception: BankingException):
        """Recovery strategy for rate limit errors."""
        logger.info("Implementing rate limit backoff")
        # Implement exponential backoff logic


# Register recovery strategies
error_handler.register_recovery_strategy(
    "DATABASE_ERROR",
    BankingErrorRecovery.database_connection_recovery
)
error_handler.register_recovery_strategy(
    "AUTHENTICATION_ERROR",
    BankingErrorRecovery.authentication_token_refresh
)
error_handler.register_recovery_strategy(
    "RATE_LIMIT_ERROR",
    BankingErrorRecovery.rate_limit_backoff
)


# Banking-specific exception classes
class AuthenticationError(BankingException):
    """Authentication-related errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.AUTHENTICATION,
            details=details,
            **kwargs
        )


class AuthorizationError(BankingException):
    """Authorization-related errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.AUTHORIZATION,
            details=details,
            **kwargs
        )


class ValidationError(BankingException):
    """Data validation errors."""
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None, **kwargs):
        if details is None:
            details = {}
        if field:
            details["field"] = field
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION,
            details=details,
            **kwargs
        )


class ComplianceError(BankingException):
    """Compliance and regulatory errors."""
    def __init__(self, message: str, regulation: Optional[str] = None, details: Optional[Dict[str, Any]] = None, **kwargs):
        if details is None:
            details = {}
        if regulation:
            details["regulation"] = regulation
        
        super().__init__(
            message=message,
            error_code="COMPLIANCE_ERROR",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.COMPLIANCE,
            details=details,
            **kwargs
        )


class SecurityError(BankingException):
    """Security-related errors."""
    def __init__(self, message: str, threat_level: str = "medium", details: Optional[Dict[str, Any]] = None, **kwargs):
        if details is None:
            details = {}
        details["threat_level"] = threat_level
        
        super().__init__(
            message=message,
            error_code="SECURITY_ERROR",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SECURITY,
            details=details,
            **kwargs
        )


# Utility functions for common error patterns
def validate_required_fields(data: Dict[str, Any], required_fields: List[str], **kwargs) -> None:
    """Validate that required fields are present in data."""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        raise ValidationError(
            message=f"Missing required fields: {', '.join(missing_fields)}",
            details={"missing_fields": missing_fields},
            **kwargs
        )


def validate_amount(amount: Union[int, float], min_amount: float = 0, max_amount: Optional[float] = None, **kwargs) -> None:
    """Validate monetary amounts for banking operations."""
    if not isinstance(amount, (int, float)) or amount < min_amount:
        raise ValidationError(
            message=f"Amount must be a number greater than or equal to {min_amount}",
            field="amount",
            details={"amount": amount, "min_amount": min_amount},
            **kwargs
        )
    
    if max_amount is not None and amount > max_amount:
        raise ValidationError(
            message=f"Amount cannot exceed {max_amount}",
            field="amount",
            details={"amount": amount, "max_amount": max_amount},
            **kwargs
        )


def validate_currency(currency: str, allowed_currencies: List[str], **kwargs) -> None:
    """Validate currency codes."""
    if currency not in allowed_currencies:
        raise ValidationError(
            message=f"Currency {currency} is not supported",
            field="currency",
            details={"currency": currency, "allowed_currencies": allowed_currencies},
            **kwargs
        )
