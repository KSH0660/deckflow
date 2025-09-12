"""
Common utilities for API endpoints.

Provides shared functionality like error handling, validation, and decorators.
"""

import functools
from typing import Any, Callable, TypeVar

from fastapi import HTTPException

from app.logging import get_logger

logger = get_logger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


def handle_service_errors(func: F) -> F:
    """
    Decorator to handle common service layer exceptions and convert them to HTTP responses.
    
    Maps:
    - ValueError -> 404 if contains "not found", otherwise 400
    - Other exceptions -> 500
    
    Usage:
        @handle_service_errors
        async def my_endpoint():
            return await service.do_something()
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                logger.warning(f"Resource not found: {error_msg}")
                raise HTTPException(status_code=404, detail=error_msg) from e
            else:
                logger.warning(f"Validation error: {error_msg}")
                raise HTTPException(status_code=400, detail=error_msg) from e
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Internal server error in {func.__name__}: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg) from e
    
    return wrapper


def handle_validation_errors(func: F) -> F:
    """
    Decorator specifically for endpoints that need custom validation error handling.
    
    Similar to handle_service_errors but with more specific logging.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            error_msg = str(e)
            logger.warning(f"Validation failed in {func.__name__}: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg) from e
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected error in {func.__name__}: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg) from e
    
    return wrapper