"""Custom exceptions for the application."""
from typing import Any

class BaseError(Exception):
    """Base error for all custom exceptions."""
    def __init__(self, message: str, **context: Any) -> None:
        self.message = message
        self.context = context
        super().__init__(message)

class ServiceError(BaseError):
    """Base error for service-level exceptions."""
    pass

class ValidationError(ServiceError):
    """Validation error."""
    pass

class StorageError(ServiceError):
    """Storage-related errors."""
    pass

class NetworkError(ServiceError):
    """Network-related errors."""
    pass

class ConfigurationError(ServiceError):
    """Configuration-related errors."""
    pass

class AuthenticationError(ServiceError):
    """Authentication-related errors."""
    pass

class APIError(ServiceError):
    """API-related errors."""
    pass

class DatabaseError(ServiceError):
    """Database-related errors."""
    pass

class TimeoutError(ServiceError):
    """Timeout-related errors."""
    pass

class RateLimitError(ServiceError):
    """Rate limit exceeded errors."""
    pass

class SecurityError(ServiceError):
    """Security-related errors."""
    pass

class DataProcessingError(ServiceError):
    """Data processing errors."""
    pass

# Error categories for specific services
class StorageServiceError(StorageError):
    """Storage service specific errors."""
    pass

class S3Error(StorageError):
    """S3-specific errors."""
    pass

class DynamoDBError(DatabaseError):
    """DynamoDB-specific errors."""
    pass

class SlackError(APIError):
    """Slack-specific errors."""
    pass

class OpenAIError(APIError):
    """OpenAI-specific errors."""
    pass

class OdooError(APIError):
    """Odoo-specific errors."""
    pass

class ExternalServiceError(APIError):
    """External service specific errors."""
    pass