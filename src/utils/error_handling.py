"""Error handling utilities."""
import functools
from typing import Any, Type, TypeVar, Callable, Optional, Dict, Union
from src.utils.logging import log_error, log_message
from src.core.exceptions import BaseError, ServiceError

T = TypeVar('T')

def handle_service_error(
    service: str,
    operation: str,
    error_type: Type[BaseError],
    **context: Any
) -> Callable[[Exception], None]:
    """
    Handle service errors consistently.
    
    Args:
        service: Service name
        operation: Operation being performed
        error_type: Type of error to raise
        **context: Additional context
        
    Returns:
        Callable: Error handler function
    """
    def handler(error: Exception) -> None:
        log_error(service, f"Error in {operation}", error, **context)
        if isinstance(error, error_type):
            raise
        raise error_type(str(error), **context) from error
    return handler

def validate_error_context(error: BaseError) -> bool:
    """
    Validate error has required context.
    
    Args:
        error: Error to validate
        
    Returns:
        bool: True if valid
    """
    required_fields = {'message', 'context'}
    return all(hasattr(error, field) for field in required_fields)

def preserve_error_chain(
    original: Exception,
    new: BaseError
) -> BaseError:
    """
    Preserve error chain while wrapping errors.
    
    Args:
        original: Original exception
        new: New error to wrap with
        
    Returns:
        BaseError: New error with preserved chain
    """
    if isinstance(original, BaseError):
        new.context.update(original.context)
    new.__cause__ = original
    return new

def with_error_recovery(
    operation: Callable[..., T],
    recovery: Callable[..., T],
    max_retries: int = 3,
    service: str = 'service'
) -> Callable[..., T]:
    """
    Decorator for operations with error recovery.
    
    Args:
        operation: Original operation
        recovery: Recovery operation
        max_retries: Maximum retry attempts
        service: Service name for logging
        
    Returns:
        Callable: Wrapped operation with recovery
    """
    @functools.wraps(operation)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        attempts = 0
        last_error = None
        
        while attempts < max_retries:
            try:
                if attempts > 0:
                    log_message('INFO', service,
                              f"Retry attempt {attempts} for {operation.__name__}")
                return operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                log_error(service,
                         f"Operation failed, attempt {attempts + 1}/{max_retries}",
                         e, operation=operation.__name__)
                attempts += 1
        
        log_message('INFO', service,
                   f"All retries failed for {operation.__name__}, attempting recovery")
        try:
            return recovery(*args, **kwargs)
        except Exception as e:
            log_error(service, "Recovery failed", e,
                     operation=operation.__name__)
            raise ServiceError(
                "Operation failed and recovery was unsuccessful",
                original_error=str(last_error),
                recovery_error=str(e)
            ) from e
    
    return wrapper

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Backoff multiplier
        exceptions: Exceptions to catch
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            import time
            
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        raise
                    
                    log_error('service',
                             f"Retry attempt {attempt + 1}/{max_retries} failed",
                             e, function=func.__name__)
                    
                    # Calculate next delay
                    delay = min(delay * backoff_factor, max_delay)
                    time.sleep(delay)
            
            # This shouldn't be reached, but just in case
            raise last_exception  # type: ignore
        
        return wrapper
    
    return decorator

def wrap_exceptions(
    target_exception: Type[BaseError],
    **context: Any
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Wrap exceptions in a specific error type.
    
    Args:
        target_exception: Exception type to wrap with
        **context: Additional context
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if isinstance(e, target_exception):
                    raise
                raise target_exception(str(e), **context) from e
        return wrapper
    return decorator

def extract_error_context(
    error: Exception,
    include_traceback: bool = False
) -> Dict[str, Any]:
    """
    Extract context from an error.
    
    Args:
        error: Exception to extract context from
        include_traceback: Whether to include traceback
        
    Returns:
        Dict[str, Any]: Error context
    """
    context: Dict[str, Any] = {
        'error_type': type(error).__name__,
        'error_message': str(error)
    }
    
    if isinstance(error, BaseError):
        context.update(error.context)
    
    if include_traceback:
        import traceback
        context['traceback'] = traceback.format_exc()
    
    return context

def safe_operation(
    default: Optional[T] = None,
    error_handler: Optional[Callable[[Exception], None]] = None
) -> Callable[[Callable[..., T]], Callable[..., Union[T, None]]]:
    """
    Decorator for safe operation execution.
    
    Args:
        default: Default value on error
        error_handler: Optional error handler
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, None]]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Union[T, None]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if error_handler:
                    error_handler(e)
                return default
        return wrapper
    return decorator