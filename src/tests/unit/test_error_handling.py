"""Tests for error handling utilities."""
import time
import pytest
from unittest.mock import patch, MagicMock
from typing import Any, Dict

from src.core.exceptions import (
    BaseError,
    ServiceError,
    ValidationError,
    StorageError,
    NetworkError
)
from src.utils.error_handling import (
    handle_service_error,
    validate_error_context,
    preserve_error_chain,
    with_error_recovery,
    retry_with_backoff,
    wrap_exceptions,
    extract_error_context,
    safe_operation
)

def test_error_hierarchy():
    """Test error inheritance."""
    assert issubclass(ServiceError, BaseError)
    assert issubclass(ValidationError, ServiceError)
    assert issubclass(StorageError, ServiceError)
    assert issubclass(NetworkError, ServiceError)

def test_error_context():
    """Test error context preservation."""
    try:
        raise StorageError("Test error", key="value")
    except StorageError as e:
        assert e.context['key'] == "value"
        assert e.message == "Test error"

def test_handle_service_error():
    """Test service error handler."""
    handler = handle_service_error(
        'test',
        'operation',
        StorageError,
        context_key="value"
    )
    
    with pytest.raises(StorageError) as exc_info:
        handler(ValueError("test error"))
    
    assert "test error" in str(exc_info.value)
    assert exc_info.value.context['context_key'] == "value"

def test_validate_error_context():
    """Test error context validation."""
    error = StorageError("test", key="value")
    assert validate_error_context(error)
    
    # Test invalid error
    class InvalidError(Exception):
        pass
    
    error = InvalidError()
    assert not validate_error_context(error)  # type: ignore

def test_preserve_error_chain():
    """Test error chain preservation."""
    original = ValidationError("original", key="original_value")
    new = StorageError("new", key="new_value")
    
    result = preserve_error_chain(original, new)
    
    assert result.__cause__ == original
    assert result.context['key'] == "new_value"
    assert 'key' in result.context

def test_error_recovery():
    """Test error recovery mechanism."""
    def operation():
        raise ValueError("test error")
    
    def recovery():
        return "recovered"
    
    decorated = with_error_recovery(operation, recovery)
    assert decorated() == "recovered"

def test_error_recovery_with_retries():
    """Test error recovery with multiple retries."""
    attempts = 0
    
    def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("retry error")
        return "success"
    
    def recovery():
        return "recovered"
    
    decorated = with_error_recovery(operation, recovery, max_retries=3)
    assert decorated() == "success"
    assert attempts == 3

def test_retry_with_backoff():
    """Test retry with exponential backoff."""
    attempts = 0
    
    @retry_with_backoff(max_retries=3, initial_delay=0.1)
    def flaky_operation():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ValueError("temporary error")
        return "success"
    
    assert flaky_operation() == "success"
    assert attempts == 2

def test_retry_with_backoff_failure():
    """Test retry with backoff eventual failure."""
    @retry_with_backoff(max_retries=3, initial_delay=0.1)
    def failing_operation():
        raise ValueError("persistent error")
    
    with pytest.raises(ValueError):
        failing_operation()

def test_wrap_exceptions():
    """Test exception wrapping."""
    @wrap_exceptions(StorageError, operation="test")
    def risky_operation():
        raise ValueError("original error")
    
    with pytest.raises(StorageError) as exc_info:
        risky_operation()
    
    assert "original error" in str(exc_info.value)
    assert exc_info.value.context['operation'] == "test"

def test_extract_error_context():
    """Test error context extraction."""
    try:
        raise StorageError("test error", key="value")
    except StorageError as e:
        context = extract_error_context(e)
        assert context['error_type'] == "StorageError"
        assert context['error_message'] == "test error"
        assert context['key'] == "value"

def test_extract_error_context_with_traceback():
    """Test error context extraction with traceback."""
    try:
        raise StorageError("test error")
    except StorageError as e:
        context = extract_error_context(e, include_traceback=True)
        assert 'traceback' in context
        assert 'test_error_context_with_traceback' in context['traceback']

def test_safe_operation():
    """Test safe operation execution."""
    @safe_operation(default="default")
    def risky_operation():
        raise ValueError("error")
    
    assert risky_operation() == "default"

def test_safe_operation_with_handler():
    """Test safe operation with custom error handler."""
    handler_called = False
    
    def error_handler(e: Exception) -> None:
        nonlocal handler_called
        handler_called = True
    
    @safe_operation(default="default", error_handler=error_handler)
    def risky_operation():
        raise ValueError("error")
    
    assert risky_operation() == "default"
    assert handler_called

def test_error_context_inheritance():
    """Test error context inheritance in error chain."""
    try:
        try:
            raise ValidationError("inner", key="inner_value")
        except ValidationError as e:
            raise StorageError("outer", key="outer_value") from e
    except StorageError as e:
        assert e.context['key'] == "outer_value"
        assert e.__cause__.context['key'] == "inner_value"  # type: ignore

def test_multiple_error_wrapping():
    """Test multiple levels of error wrapping."""
    @wrap_exceptions(ValidationError, level="inner")
    def inner_operation():
        raise ValueError("inner error")
    
    @wrap_exceptions(StorageError, level="outer")
    def outer_operation():
        inner_operation()
    
    with pytest.raises(StorageError) as exc_info:
        outer_operation()
    
    assert exc_info.value.context['level'] == "outer"
    assert isinstance(exc_info.value.__cause__, ValidationError)
    assert exc_info.value.__cause__.context['level'] == "inner"  # type: ignore

def test_error_recovery_chain():
    """Test error recovery with error chain preservation."""
    def operation():
        try:
            raise ValueError("original")
        except ValueError as e:
            raise StorageError("wrapped", original=str(e))
    
    def recovery():
        return "recovered"
    
    decorated = with_error_recovery(operation, recovery)
    assert decorated() == "recovered"

@pytest.mark.parametrize("error_class,expected_base", [
    (ValidationError, ServiceError),
    (StorageError, ServiceError),
    (NetworkError, ServiceError),
    (ServiceError, BaseError)
])
def test_error_hierarchy_relationships(error_class: Any, expected_base: Any):
    """Test error hierarchy relationships."""
    assert issubclass(error_class, expected_base)
    assert issubclass(error_class, BaseError)

def test_error_str_representation():
    """Test error string representation."""
    error = StorageError("test message", key="value")
    assert str(error) == "test message"
    assert repr(error).startswith("<StorageError")

def test_error_context_immutability():
    """Test error context immutability."""
    original_context = {"key": "value"}
    error = StorageError("test", **original_context)
    
    # Modifying the original context shouldn't affect the error
    original_context["key"] = "modified"
    assert error.context["key"] == "value"

def test_nested_error_handling():
    """Test nested error handling with context preservation."""
    def inner_handler(e: Exception) -> None:
        raise ValidationError("inner error", inner_key="inner_value") from e
    
    def outer_handler(e: Exception) -> None:
        try:
            inner_handler(e)
        except ValidationError as ve:
            raise StorageError("outer error", outer_key="outer_value") from ve
    
    with pytest.raises(StorageError) as exc_info:
        try:
            raise ValueError("original error")
        except ValueError as e:
            outer_handler(e)
    
    error = exc_info.value
    assert error.context["outer_key"] == "outer_value"
    assert isinstance(error.__cause__, ValidationError)
    assert error.__cause__.context["inner_key"] == "inner_value"  # type: ignore