"""Tests for logging utilities."""
import re
import time
from unittest.mock import patch, MagicMock
import pytest
from src.utils.logging import (
    log_message,
    log_error,
    validate_log_format,
    sanitize_context,
    rate_limited_log
)

@pytest.fixture
def capture_logs():
    """Fixture to capture log output."""
    logs = []
    with patch('builtins.print') as mock_print:
        mock_print.side_effect = logs.append
        yield logs

def test_log_message_format(capture_logs):
    """Test log message format."""
    log_message('INFO', 'test', 'Test message', key='value')
    assert len(capture_logs) == 1
    assert validate_log_format(capture_logs[0])

def test_log_error_format(capture_logs):
    """Test error log format."""
    error = ValueError('test error')
    log_error('test', 'Error occurred', error, context='test')
    assert len(capture_logs) == 1
    assert validate_log_format(capture_logs[0])
    assert 'error_type=ValueError' in capture_logs[0]
    assert 'error_details=test error' in capture_logs[0]

def test_log_format_validation():
    """Test log format validation."""
    valid_log = '2025-02-24 01:00:00 [INFO] [test] Message key=value'
    invalid_log = 'Invalid log format'
    
    assert validate_log_format(valid_log)
    assert not validate_log_format(invalid_log)

def test_context_sanitization():
    """Test context value sanitization."""
    context = {
        'normal': 'value',
        'newlines': 'line1\nline2',
        'long': 'x' * 2000,
        'special': 'value=with=equals'
    }
    
    sanitized = sanitize_context(**context)
    
    assert len(sanitized['long']) == 1000  # Truncated
    assert '\n' not in sanitized['newlines']  # Escaped
    assert sanitized['normal'] == 'value'  # Unchanged
    assert '=' in sanitized['special']  # Preserved

def test_rate_limiting():
    """Test rate limited logging."""
    logs = []
    with patch('builtins.print') as mock_print:
        mock_print.side_effect = logs.append
        
        # First log should go through
        rate_limited_log('INFO', 'test', 'message', max_per_second=1)
        assert len(logs) == 1
        
        # Second immediate log should be rate limited
        rate_limited_log('INFO', 'test', 'message', max_per_second=1)
        assert len(logs) == 1
        
        # After waiting, log should go through
        time.sleep(1.1)
        rate_limited_log('INFO', 'test', 'message', max_per_second=1)
        assert len(logs) == 2

def test_log_message_with_empty_context(capture_logs):
    """Test logging message without context."""
    log_message('INFO', 'test', 'Test message')
    assert len(capture_logs) == 1
    assert validate_log_format(capture_logs[0])

def test_log_message_with_complex_context(capture_logs):
    """Test logging message with complex context."""
    context = {
        'dict': {'key': 'value'},
        'list': [1, 2, 3],
        'none': None,
        'bool': True
    }
    log_message('INFO', 'test', 'Test message', **context)
    assert len(capture_logs) == 1
    assert validate_log_format(capture_logs[0])

def test_log_levels(capture_logs):
    """Test different log levels."""
    levels = ['INFO', 'ERROR', 'WARN', 'DEBUG']
    for level in levels:
        log_message(level, 'test', f'{level} message')
    
    assert len(capture_logs) == len(levels)
    for log, level in zip(capture_logs, levels):
        assert f'[{level}]' in log

def test_timestamp_format(capture_logs):
    """Test timestamp format in logs."""
    log_message('INFO', 'test', 'Test message')
    assert len(capture_logs) == 1
    
    timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
    assert re.match(timestamp_pattern, capture_logs[0].split()[0])

def test_service_name_format(capture_logs):
    """Test service name format in logs."""
    services = ['test', 'service-name', 'complex.service.name']
    for service in services:
        log_message('INFO', service, 'Test message')
    
    assert len(capture_logs) == len(services)
    for log, service in zip(capture_logs, services):
        assert f'[{service}]' in log

def test_error_context_preservation(capture_logs):
    """Test error context is preserved in error logs."""
    try:
        raise ValueError('test error')
    except ValueError as e:
        log_error('test', 'Error occurred', e, extra='context')
    
    assert len(capture_logs) == 1
    log = capture_logs[0]
    assert 'error_type=ValueError' in log
    assert 'error_details=test error' in log
    assert 'extra=context' in log

def test_rate_limiting_different_messages():
    """Test rate limiting with different messages."""
    logs = []
    with patch('builtins.print') as mock_print:
        mock_print.side_effect = logs.append
        
        # Different messages should not be rate limited
        rate_limited_log('INFO', 'test', 'message1', max_per_second=1)
        rate_limited_log('INFO', 'test', 'message2', max_per_second=1)
        assert len(logs) == 2

def test_rate_limiting_different_services():
    """Test rate limiting with different services."""
    logs = []
    with patch('builtins.print') as mock_print:
        mock_print.side_effect = logs.append
        
        # Different services should not be rate limited
        rate_limited_log('INFO', 'service1', 'message', max_per_second=1)
        rate_limited_log('INFO', 'service2', 'message', max_per_second=1)
        assert len(logs) == 2

def test_rate_limiting_different_levels():
    """Test rate limiting with different levels."""
    logs = []
    with patch('builtins.print') as mock_print:
        mock_print.side_effect = logs.append
        
        # Different levels should not be rate limited
        rate_limited_log('INFO', 'test', 'message', max_per_second=1)
        rate_limited_log('ERROR', 'test', 'message', max_per_second=1)
        assert len(logs) == 2