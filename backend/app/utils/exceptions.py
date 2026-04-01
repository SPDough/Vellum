"""
Shared exception handling utilities for API endpoints.
"""

from functools import wraps
from typing import Any, Callable

from fastapi import HTTPException, status


def handle_service_exceptions(func: Callable) -> Callable:
    """
    Decorator to handle common service exceptions in API endpoints.
    Catches HTTPException and re-raises, catches other exceptions and converts to HTTP 500.
    """

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal service error: {str(e)}",
            )

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal service error: {str(e)}",
            )

    # Return appropriate wrapper based on function type
    import asyncio
    import inspect

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def handle_endpoint_exceptions(detail_prefix: str = "Service error"):
    """
    Context manager or inline exception handler for endpoints.
    Usage in endpoints to replace try/except blocks.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"{detail_prefix}: {str(e)}",
                )

        return wrapper

    return decorator
