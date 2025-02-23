import pytest
from src.core.exceptions import (
    BaseError,
    ConfigurationError,
    APIError,
    ValidationError,
    StorageError,
    AuthenticationError,
    RateLimitError,
    ResourceNotFoundError,
    ServiceUnavailableError,
    DataProcessingError,
    NetworkError,
    TimeoutError,
    SecurityError,
    InputError,
    DatabaseError,
    handle_error
)

def test_base_error_with_message():
    """Test BaseError with message only."""
    error = BaseError("Test error")
    assert error.message == "Test error"
    assert error.code is None
    assert error.details is None
    assert str(error) == "Test error"

def test_base_error_with_all_args():
    """Test BaseError with all arguments."""
    error = BaseError("Test error", "TEST_ERROR", {"key": "value"})
    assert error.message == "Test error"
    assert error.code == "TEST_ERROR"
    assert error.details == {"key": "value"}

@pytest.mark.parametrize("error_class", [
    ConfigurationError,
    APIError,
    ValidationError,
    StorageError,
    AuthenticationError,
    RateLimitError,
    ResourceNotFoundError,
    ServiceUnavailableError,
    DataProcessingError,
    NetworkError,
    TimeoutError,
    SecurityError,
    InputError,
    DatabaseError
])
def test_custom_errors(error_class):
    """Test all custom error classes."""
    error = error_class("Test error", "TEST_ERROR", {"key": "value"})
    assert isinstance(error, BaseError)
    assert error.message == "Test error"
    assert error.code == "TEST_ERROR"
    assert error.details == {"key": "value"}

def test_handle_error_base_error():
    """Test handling BaseError."""
    error = BaseError("Test error", "TEST_ERROR", {"key": "value"})
    result = handle_error(error)
    assert result == {
        'status': 'error',
        'code': 'TEST_ERROR',
        'message': 'Test error',
        'details': {'key': 'value'}
    }

def test_handle_error_base_error_no_code():
    """Test handling BaseError without code."""
    error = BaseError("Test error")
    result = handle_error(error)
    assert result == {
        'status': 'error',
        'code': 'BaseError',
        'message': 'Test error',
        'details': None
    }

def test_handle_error_value_error():
    """Test handling ValueError."""
    error = ValueError("Invalid value")
    result = handle_error(error)
    assert result == {
        'status': 'error',
        'code': 'ValueError',
        'message': 'Invalid value',
        'details': None
    }

def test_handle_error_type_error():
    """Test handling TypeError."""
    error = TypeError("Invalid type")
    result = handle_error(error)
    assert result == {
        'status': 'error',
        'code': 'TypeError',
        'message': 'Invalid type',
        'details': None
    }

def test_handle_error_key_error():
    """Test handling KeyError."""
    error = KeyError("missing_key")
    result = handle_error(error)
    assert result == {
        'status': 'error',
        'code': 'KeyError',
        'message': "'missing_key'",
        'details': None
    }

def test_handle_error_unknown():
    """Test handling unknown error type."""
    class UnknownError(Exception):
        pass
    
    error = UnknownError("Unknown error")
    result = handle_error(error)
    assert result == {
        'status': 'error',
        'code': 'UnhandledError',
        'message': 'Unknown error',
        'details': None
    }

@pytest.mark.parametrize("error_class,expected_code", [
    (ConfigurationError, "ConfigurationError"),
    (APIError, "APIError"),
    (ValidationError, "ValidationError"),
    (StorageError, "StorageError"),
    (AuthenticationError, "AuthenticationError"),
    (RateLimitError, "RateLimitError"),
    (ResourceNotFoundError, "ResourceNotFoundError"),
    (ServiceUnavailableError, "ServiceUnavailableError"),
    (DataProcessingError, "DataProcessingError"),
    (NetworkError, "NetworkError"),
    (TimeoutError, "TimeoutError"),
    (SecurityError, "SecurityError"),
    (InputError, "InputError"),
    (DatabaseError, "DatabaseError")
])
def test_error_handling_all_types(error_class, expected_code):
    """Test handling all error types."""
    error = error_class("Test error")
    result = handle_error(error)
    assert result == {
        'status': 'error',
        'code': expected_code,
        'message': 'Test error',
        'details': None
    }

def test_error_inheritance():
    """Test error class inheritance."""
    errors = [
        ConfigurationError,
        APIError,
        ValidationError,
        StorageError,
        AuthenticationError,
        RateLimitError,
        ResourceNotFoundError,
        ServiceUnavailableError,
        DataProcessingError,
        NetworkError,
        TimeoutError,
        SecurityError,
        InputError,
        DatabaseError
    ]
    
    for error_class in errors:
        error = error_class("Test")
        assert isinstance(error, BaseError)
        assert isinstance(error, Exception)