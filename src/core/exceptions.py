from typing import Optional, Any

class BaseError(Exception):
    """Base class for all custom exceptions."""
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Any] = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)

class ConfigurationError(BaseError):
    """Raised when there is a configuration-related error."""
    pass

class APIError(BaseError):
    """Raised when an API request fails."""
    pass

class ValidationError(BaseError):
    """Raised when data validation fails."""
    pass

class StorageError(BaseError):
    """Raised when storage operations fail."""
    pass

class AuthenticationError(BaseError):
    """Raised when authentication fails."""
    pass

class RateLimitError(BaseError):
    """Raised when rate limits are exceeded."""
    pass

class ResourceNotFoundError(BaseError):
    """Raised when a requested resource is not found."""
    pass

class ServiceUnavailableError(BaseError):
    """Raised when a service is unavailable."""
    pass

class DataProcessingError(BaseError):
    """Raised when data processing fails."""
    pass

class NetworkError(BaseError):
    """Raised when network operations fail."""
    pass

class TimeoutError(BaseError):
    """Raised when an operation times out."""
    pass

class SecurityError(BaseError):
    """Raised when a security-related error occurs."""
    pass

class InputError(BaseError):
    """Raised when input validation fails."""
    pass

class DatabaseError(BaseError):
    """Raised when database operations fail."""
    pass

def handle_error(error: Exception) -> dict:
    """
    Handles exceptions and returns a standardized error response.
    
    Args:
        error: The exception to handle
        
    Returns:
        dict: Standardized error response
    """
    if isinstance(error, BaseError):
        return {
            'status': 'error',
            'code': error.code or error.__class__.__name__,
            'message': error.message,
            'details': error.details
        }
    
    # Handle standard Python exceptions
    if isinstance(error, ValueError):
        return {
            'status': 'error',
            'code': 'ValueError',
            'message': str(error),
            'details': None
        }
    elif isinstance(error, TypeError):
        return {
            'status': 'error',
            'code': 'TypeError',
            'message': str(error),
            'details': None
        }
    elif isinstance(error, KeyError):
        return {
            'status': 'error',
            'code': 'KeyError',
            'message': str(error),
            'details': None
        }
    
    # Generic error handler
    return {
        'status': 'error',
        'code': 'UnhandledError',
        'message': str(error),
        'details': None
    }