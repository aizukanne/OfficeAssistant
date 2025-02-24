"""Logging utilities for Lambda-compatible logging."""
import time
import re
from typing import Any, Dict

def log_message(
    level: str,
    service: str,
    message: str,
    **context: Any
) -> None:
    """
    Log a message in CloudWatch format.
    
    Args:
        level: Log level (INFO, ERROR, etc.)
        service: Service name
        message: Log message
        **context: Additional context as key-value pairs
    """
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    sanitized_context = sanitize_context(**context)
    context_str = ' '.join(f"{k}={v}" for k, v in sorted(sanitized_context.items()))
    print(f"{timestamp} [{level}] [{service}] {message} {context_str}")

def log_error(
    service: str,
    message: str,
    error: Exception,
    **context: Any
) -> None:
    """
    Log an error with exception details.
    
    Args:
        service: Service name
        message: Error message
        error: Exception object
        **context: Additional context
    """
    context['error_type'] = error.__class__.__name__
    context['error_details'] = str(error)
    log_message('ERROR', service, message, **context)

def validate_log_format(log_line: str) -> bool:
    """
    Validate log line format.
    
    Args:
        log_line: Log line to validate
        
    Returns:
        bool: True if format is valid
    """
    pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[(INFO|ERROR|WARN|DEBUG)\] \[[^\]]+\] .+'
    return bool(re.match(pattern, log_line))

def sanitize_context(**context: Any) -> Dict[str, str]:
    """
    Sanitize context values for logging.
    
    Args:
        **context: Context key-value pairs
        
    Returns:
        Dict[str, str]: Sanitized context
    """
    return {
        k: str(v).replace('\n', '\\n')[:1000]
        for k, v in context.items()
    }

_log_timestamps: Dict[str, float] = {}

def rate_limited_log(
    level: str,
    service: str,
    message: str,
    max_per_second: int = 10
) -> None:
    """
    Rate limited logging.
    
    Args:
        level: Log level
        service: Service name
        message: Log message
        max_per_second: Maximum logs per second
    """
    current_time = time.time()
    key = f"{level}:{service}:{message}"
    
    if key in _log_timestamps:
        time_diff = current_time - _log_timestamps[key]
        if time_diff < (1.0 / max_per_second):
            return
    
    _log_timestamps[key] = current_time
    log_message(level, service, message)