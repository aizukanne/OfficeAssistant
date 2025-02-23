import time
import hashlib
import threading
from typing import Dict, Optional, Any, Callable
from functools import wraps
from datetime import datetime

from src.core.exceptions import (
    RateLimitError,
    SecurityError,
    ValidationError
)
from src.core.logging import ServiceLogger

# Initialize logger
logger = ServiceLogger('security')

class RateLimiter:
    """Rate limiting implementation using token bucket algorithm."""
    
    def __init__(self, rate: int, capacity: int):
        """
        Initialize rate limiter.
        
        Args:
            rate: Tokens per second
            capacity: Maximum token capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def _add_tokens(self) -> None:
        """Add tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        new_tokens = elapsed * self.rate
        
        with self.lock:
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_update = now
    
    def acquire(self, tokens: int = 1) -> bool:
        """
        Attempt to acquire tokens.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            bool: True if tokens were acquired
        """
        self._add_tokens()
        
        with self.lock:
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

class RequestValidator:
    """Request validation and sanitization."""
    
    @staticmethod
    def validate_input(data: Any, schema: Dict) -> None:
        """
        Validate input against schema.
        
        Args:
            data: Input data to validate
            schema: Validation schema
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(schema, dict):
            raise ValueError("Schema must be a dictionary")
            
        if 'type' not in schema:
            raise ValueError("Schema must specify type")
            
        # Validate type
        expected_type = schema['type']
        if expected_type == 'object':
            if not isinstance(data, dict):
                raise ValidationError("Expected object")
                
            # Validate required fields
            required = schema.get('required', [])
            for field in required:
                if field not in data:
                    raise ValidationError(f"Missing required field: {field}")
                    
            # Validate properties
            properties = schema.get('properties', {})
            for field, value in data.items():
                if field in properties:
                    try:
                        RequestValidator.validate_input(value, properties[field])
                    except ValidationError as e:
                        raise ValidationError(f"Invalid field {field}: {str(e)}")
                        
        elif expected_type == 'array':
            if not isinstance(data, (list, tuple)):
                raise ValidationError("Expected array")
                
            # Validate array items
            if 'items' in schema:
                for item in data:
                    RequestValidator.validate_input(item, schema['items'])
                    
        elif expected_type == 'string':
            if not isinstance(data, str):
                raise ValidationError("Expected string")
                
        elif expected_type == 'number':
            if not isinstance(data, (int, float)):
                raise ValidationError("Expected number")
                
        elif expected_type == 'boolean':
            if not isinstance(data, bool):
                raise ValidationError("Expected boolean")
    
    @staticmethod
    def sanitize_input(data: Any) -> Any:
        """
        Sanitize input data.
        
        Args:
            data: Input data to sanitize
            
        Returns:
            Any: Sanitized data
        """
        if isinstance(data, str):
            # Remove potentially dangerous characters
            return data.replace('<', '&lt;').replace('>', '&gt;')
        elif isinstance(data, dict):
            return {k: RequestValidator.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [RequestValidator.sanitize_input(x) for x in data]
        return data

class AuditLogger:
    """Audit logging implementation."""
    
    def __init__(self):
        """Initialize audit logger."""
        self.logger = ServiceLogger('audit')
    
    def log_request(
        self,
        method: str,
        path: str,
        user: Optional[str] = None,
        data: Optional[Dict] = None
    ) -> None:
        """
        Log an API request.
        
        Args:
            method: HTTP method
            path: Request path
            user: Optional user identifier
            data: Optional request data
        """
        self.logger.info(
            "API Request",
            method=method,
            path=path,
            user=user,
            data=data
        )
    
    def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any]
    ) -> None:
        """
        Log a security event.
        
        Args:
            event_type: Type of security event
            details: Event details
        """
        self.logger.warning(
            "Security Event",
            event_type=event_type,
            **details
        )

# Global instances
rate_limiter = RateLimiter(100, 1000)  # 100 requests per second, burst of 1000
request_validator = RequestValidator()
audit_logger = AuditLogger()

def rate_limit(tokens: int = 1):
    """
    Rate limiting decorator.
    
    Args:
        tokens: Number of tokens required
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not rate_limiter.acquire(tokens):
                raise RateLimitError("Rate limit exceeded")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate_request(schema: Dict):
    """
    Request validation decorator.
    
    Args:
        schema: Validation schema
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validate input
            try:
                request_data = kwargs.get('data', {})
                request_validator.validate_input(request_data, schema)
                kwargs['data'] = request_validator.sanitize_input(request_data)
            except ValidationError as e:
                raise SecurityError(f"Request validation failed: {str(e)}")
            
            # Log request
            audit_logger.log_request(
                method=kwargs.get('method', 'UNKNOWN'),
                path=kwargs.get('path', 'UNKNOWN'),
                user=kwargs.get('user'),
                data=kwargs.get('data')
            )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def audit_log(event_type: str):
    """
    Audit logging decorator.
    
    Args:
        event_type: Type of event to log
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                audit_logger.log_security_event(
                    event_type,
                    {
                        'status': 'success',
                        'args': args,
                        'kwargs': kwargs,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                return result
            except Exception as e:
                audit_logger.log_security_event(
                    event_type,
                    {
                        'status': 'error',
                        'error': str(e),
                        'args': args,
                        'kwargs': kwargs,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                raise
        return wrapper
    return decorator