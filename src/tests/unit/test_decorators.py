"""Tests for logging decorators."""
import time
from unittest.mock import patch, MagicMock
import pytest
from src.utils.decorators import (
    log_function_call,
    log_error_decorator,
    log_performance
)

@pytest.fixture
def capture_logs():
    """Fixture to capture log output."""
    logs = []
    with patch('builtins.print') as mock_print:
        mock_print.side_effect = logs.append
        yield logs

def test_log_function_call_success(capture_logs):
    """Test successful function call logging."""
    @log_function_call('test')
    def test_function(arg1, arg2, kwarg1="default"):
        return "success"
    
    result = test_function("val1", "val2", kwarg1="custom")
    
    assert result == "success"
    assert len(capture_logs) == 1
    assert '[INFO]' in capture_logs[0]
    assert '[test]' in capture_logs[0]
    assert 'Called test_function' in capture_logs[0]
    assert 'duration=' in capture_logs[0]

def test_log_function_call_error(capture_logs):
    """Test function call logging with error."""
    @log_function_call('test')
    def test_function():
        raise ValueError("test error")
    
    with pytest.raises(ValueError):
        test_function()
    
    assert len(capture_logs) == 1
    assert '[ERROR]' in capture_logs[0]
    assert '[test]' in capture_logs[0]
    assert 'Error in test_function' in capture_logs[0]
    assert 'error_type=ValueError' in capture_logs[0]

def test_log_error_decorator_success(capture_logs):
    """Test error decorator with successful function."""
    @log_error_decorator('test')
    def test_function():
        return "success"
    
    result = test_function()
    
    assert result == "success"
    assert len(capture_logs) == 0  # No error, no log

def test_log_error_decorator_error(capture_logs):
    """Test error decorator with failing function."""
    @log_error_decorator('test')
    def test_function():
        raise ValueError("test error")
    
    with pytest.raises(ValueError):
        test_function()
    
    assert len(capture_logs) == 1
    assert '[ERROR]' in capture_logs[0]
    assert '[test]' in capture_logs[0]
    assert 'Error in test_function' in capture_logs[0]
    assert 'error_type=ValueError' in capture_logs[0]

def test_log_performance_success(capture_logs):
    """Test performance logging with successful function."""
    @log_performance('test', 'operation')
    def test_function():
        time.sleep(0.1)
        return "success"
    
    result = test_function()
    
    assert result == "success"
    assert len(capture_logs) == 1
    assert '[INFO]' in capture_logs[0]
    assert '[test]' in capture_logs[0]
    assert 'Performance: operation' in capture_logs[0]
    assert 'duration=' in capture_logs[0]
    assert 'operation=operation' in capture_logs[0]

def test_log_performance_error(capture_logs):
    """Test performance logging with failing function."""
    @log_performance('test', 'operation')
    def test_function():
        time.sleep(0.1)
        raise ValueError("test error")
    
    with pytest.raises(ValueError):
        test_function()
    
    assert len(capture_logs) == 1
    assert '[ERROR]' in capture_logs[0]
    assert '[test]' in capture_logs[0]
    assert 'Performance error: operation' in capture_logs[0]
    assert 'duration=' in capture_logs[0]
    assert 'operation=operation' in capture_logs[0]

def test_decorator_chaining(capture_logs):
    """Test multiple decorators working together."""
    @log_function_call('test')
    @log_error_decorator('test')
    @log_performance('test', 'operation')
    def test_function():
        return "success"
    
    result = test_function()
    
    assert result == "success"
    assert len(capture_logs) == 2  # Performance log and function call log
    assert any('Performance: operation' in log for log in capture_logs)
    assert any('Called test_function' in log for log in capture_logs)

def test_decorator_context_preservation():
    """Test function context is preserved by decorators."""
    @log_function_call('test')
    def test_function():
        """Test docstring."""
        return "success"
    
    assert test_function.__name__ == 'test_function'
    assert test_function.__doc__ == 'Test docstring.'

def test_nested_exceptions(capture_logs):
    """Test handling of nested exceptions."""
    @log_error_decorator('test')
    def inner_function():
        raise ValueError("inner error")
    
    @log_error_decorator('test')
    def outer_function():
        try:
            inner_function()
        except ValueError:
            raise RuntimeError("outer error")
    
    with pytest.raises(RuntimeError):
        outer_function()
    
    assert len(capture_logs) == 2
    assert any('inner error' in log for log in capture_logs)
    assert any('outer error' in log for log in capture_logs)

def test_async_function_logging(capture_logs):
    """Test logging with async functions."""
    import asyncio
    
    @log_function_call('test')
    async def test_function():
        await asyncio.sleep(0.1)
        return "success"
    
    result = asyncio.run(test_function())
    
    assert result == "success"
    assert len(capture_logs) == 1
    assert '[INFO]' in capture_logs[0]
    assert 'Called test_function' in capture_logs[0]

def test_generator_function_logging(capture_logs):
    """Test logging with generator functions."""
    @log_function_call('test')
    def test_generator():
        yield "value1"
        yield "value2"
    
    gen = test_generator()
    values = list(gen)
    
    assert values == ["value1", "value2"]
    assert len(capture_logs) == 1
    assert '[INFO]' in capture_logs[0]
    assert 'Called test_generator' in capture_logs[0]

def test_method_logging(capture_logs):
    """Test logging with class methods."""
    class TestClass:
        @log_function_call('test')
        def test_method(self, arg):
            return f"success-{arg}"
    
    obj = TestClass()
    result = obj.test_method("test")
    
    assert result == "success-test"
    assert len(capture_logs) == 1
    assert '[INFO]' in capture_logs[0]
    assert 'Called test_method' in capture_logs[0]