import os
import pytest
import logging
from unittest.mock import patch, MagicMock, call
from src.core.logging import (
    setup_logger,
    ServiceLogger,
    log_function_call,
    log_error
)

def test_setup_logger_console_only():
    """Test logger setup with console handler only."""
    logger = setup_logger("test_logger")
    
    assert logger.name == "test_logger"
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)

def test_setup_logger_with_file():
    """Test logger setup with both console and file handlers."""
    log_file = "test.log"
    logger = setup_logger("test_logger", log_file)
    
    assert len(logger.handlers) == 2
    assert isinstance(logger.handlers[0], logging.StreamHandler)
    assert isinstance(logger.handlers[1], logging.handlers.RotatingFileHandler)
    
    # Clean up
    if os.path.exists(log_file):
        os.remove(log_file)

def test_setup_logger_custom_level():
    """Test logger setup with custom log level."""
    logger = setup_logger("test_logger", level=logging.DEBUG)
    assert logger.level == logging.DEBUG

def test_setup_logger_custom_format():
    """Test logger setup with custom format."""
    custom_format = '%(levelname)s - %(message)s'
    logger = setup_logger("test_logger", format_string=custom_format)
    
    formatter = logger.handlers[0].formatter
    assert formatter._fmt == custom_format

def test_service_logger_creation():
    """Test ServiceLogger initialization."""
    logger = ServiceLogger("test_service")
    assert logger.service_name == "test_service"
    assert hasattr(logger, "logger")

@pytest.mark.parametrize("log_level,method_name", [
    ("info", "info"),
    ("error", "error"),
    ("warning", "warning"),
    ("debug", "debug"),
    ("critical", "critical")
])
def test_service_logger_levels(log_level, method_name):
    """Test all logging levels of ServiceLogger."""
    logger = ServiceLogger("test_service")
    mock_logger = MagicMock()
    logger.logger = mock_logger
    
    # Get the method by name
    log_method = getattr(logger, method_name)
    
    # Test without kwargs
    log_method("test message")
    getattr(mock_logger, method_name).assert_called_with("test message")
    
    # Test with kwargs
    log_method("test message", key="value")
    getattr(mock_logger, method_name).assert_called_with("test message [key=value]")

def test_service_logger_format_message():
    """Test message formatting in ServiceLogger."""
    logger = ServiceLogger("test_service")
    
    # Test without kwargs
    msg = logger._format_message("test message")
    assert msg == "test message"
    
    # Test with single kwarg
    msg = logger._format_message("test message", key="value")
    assert msg == "test message [key=value]"
    
    # Test with multiple kwargs
    msg = logger._format_message("test message", key1="value1", key2="value2")
    assert "key1=value1" in msg
    assert "key2=value2" in msg

@patch('src.core.logging.ServiceLogger')
def test_log_function_call_decorator(mock_logger):
    """Test log_function_call decorator."""
    logger = mock_logger()
    
    @log_function_call(logger)
    def test_function(arg1, arg2, kwarg1="default"):
        return "result"
    
    result = test_function("val1", "val2", kwarg1="custom")
    
    assert result == "result"
    logger.debug.assert_has_calls([
        call("Calling test_function", args=("val1", "val2"), kwargs={"kwarg1": "custom"}),
        call("test_function completed successfully")
    ])

@patch('src.core.logging.ServiceLogger')
def test_log_function_call_decorator_with_error(mock_logger):
    """Test log_function_call decorator with error."""
    logger = mock_logger()
    
    @log_function_call(logger)
    def test_function():
        raise ValueError("test error")
    
    with pytest.raises(ValueError):
        test_function()
    
    logger.debug.assert_called_once_with(
        "Calling test_function",
        args=(),
        kwargs={}
    )
    logger.error.assert_called_once_with(
        "test_function failed",
        error="test error"
    )

@patch('src.core.logging.ServiceLogger')
def test_log_error_decorator(mock_logger):
    """Test log_error decorator."""
    logger = mock_logger()
    
    @log_error(logger)
    def test_function():
        raise ValueError("test error")
    
    with pytest.raises(ValueError):
        test_function()
    
    logger.error.assert_called_once_with(
        "Error in test_function",
        error="test error",
        error_type="ValueError"
    )

def test_log_rotation():
    """Test log file rotation."""
    log_file = "test_rotation.log"
    max_bytes = 1024  # 1KB
    backup_count = 3
    
    logger = setup_logger(
        "test_logger",
        log_file,
        format_string="%(message)s"  # Simple format for predictable size
    )
    
    # Get the RotatingFileHandler
    handler = logger.handlers[1]
    handler.maxBytes = max_bytes
    handler.backupCount = backup_count
    
    # Write enough data to trigger multiple rotations
    message = "X" * (max_bytes // 2)  # Each write will be half the max size
    for i in range(10):  # Should create main log + backups
        logger.info(message)
    
    # Check that we have the expected number of backup files
    base_files = [log_file]
    backup_files = [f"{log_file}.{i}" for i in range(1, backup_count + 1)]
    
    for file in base_files + backup_files:
        assert os.path.exists(file)
        
    # Clean up
    for file in base_files + backup_files:
        if os.path.exists(file):
            os.remove(file)

def test_logger_independence():
    """Test that different loggers don't interfere with each other."""
    logger1 = ServiceLogger("service1")
    logger2 = ServiceLogger("service2")
    
    assert logger1.service_name != logger2.service_name
    assert logger1.logger != logger2.logger

def test_logger_thread_safety():
    """Test logger thread safety."""
    import threading
    import queue
    
    logger = ServiceLogger("test_service")
    message_queue = queue.Queue()
    
    def log_messages():
        for i in range(100):
            logger.info(f"Message {i}")
            message_queue.put(i)
    
    # Create multiple threads that log messages
    threads = [
        threading.Thread(target=log_messages)
        for _ in range(5)
    ]
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify we got all messages
    messages = []
    while not message_queue.empty():
        messages.append(message_queue.get())
    
    assert len(messages) == 500  # 5 threads * 100 messages