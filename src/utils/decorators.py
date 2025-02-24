"""Logging decorators for function calls."""
import functools
import time
from typing import Any, Callable

from .logging import log_message, log_error

def log_function_call(service: str) -> Callable:
    """
    Log function calls with timing.
    
    Args:
        service: Service name
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log_message('INFO', service, f"Called {func.__name__}",
                          duration=f"{duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                log_error(service, f"Error in {func.__name__}", e,
                         duration=f"{duration:.3f}s")
                raise
        return wrapper
    return decorator

def log_error_decorator(service: str) -> Callable:
    """
    Log errors from function calls.
    
    Args:
        service: Service name
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_error(service, f"Error in {func.__name__}", e)
                raise
        return wrapper
    return decorator

def log_performance(service: str, operation: str) -> Callable:
    """
    Log performance metrics for function calls.
    
    Args:
        service: Service name
        operation: Operation name
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log_message('INFO', service, f"Performance: {operation}",
                          duration=f"{duration:.3f}s",
                          operation=operation)
                return result
            except Exception as e:
                duration = time.time() - start_time
                log_error(service, f"Performance error: {operation}", e,
                         duration=f"{duration:.3f}s",
                         operation=operation)
                raise
        return wrapper
    return decorator