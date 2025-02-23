import pytest
import time
from unittest.mock import patch, MagicMock
from src.core.security import (
    RateLimiter,
    RequestValidator,
    AuditLogger,
    rate_limit,
    validate_request,
    audit_log
)
from src.core.exceptions import (
    RateLimitError,
    SecurityError,
    ValidationError
)

@pytest.fixture
def rate_limiter():
    """Create RateLimiter instance."""
    return RateLimiter(10, 100)  # 10 tokens per second, 100 max

@pytest.fixture
def audit_logger():
    """Create AuditLogger instance."""
    return AuditLogger()

def test_rate_limiter_initialization(rate_limiter):
    """Test rate limiter initialization."""
    assert rate_limiter.rate == 10
    assert rate_limiter.capacity == 100
    assert rate_limiter.tokens == 100

def test_rate_limiter_acquire_success(rate_limiter):
    """Test successful token acquisition."""
    assert rate_limiter.acquire(1) is True
    assert rate_limiter.tokens == 99

def test_rate_limiter_acquire_failure(rate_limiter):
    """Test token acquisition failure."""
    rate_limiter.tokens = 0
    assert rate_limiter.acquire(1) is False

def test_rate_limiter_token_replenishment(rate_limiter):
    """Test token replenishment over time."""
    rate_limiter.tokens = 0
    rate_limiter.last_update = time.time() - 1  # 1 second ago
    
    # Should have gained 10 tokens (rate = 10/s)
    assert rate_limiter.acquire(5) is True
    assert rate_limiter.tokens >= 4  # Approximately 5 tokens remaining

def test_rate_limiter_max_capacity(rate_limiter):
    """Test token capacity limit."""
    time.sleep(0.1)  # Allow some tokens to accumulate
    assert rate_limiter.tokens <= rate_limiter.capacity

def test_request_validator_object_validation():
    """Test object validation."""
    schema = {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'age': {'type': 'number'}
        },
        'required': ['name']
    }
    
    # Valid data
    RequestValidator.validate_input({'name': 'test'}, schema)
    
    # Missing required field
    with pytest.raises(ValidationError):
        RequestValidator.validate_input({}, schema)
    
    # Invalid type
    with pytest.raises(ValidationError):
        RequestValidator.validate_input({'name': 123}, schema)

def test_request_validator_array_validation():
    """Test array validation."""
    schema = {
        'type': 'array',
        'items': {
            'type': 'string'
        }
    }
    
    # Valid data
    RequestValidator.validate_input(['test1', 'test2'], schema)
    
    # Invalid item type
    with pytest.raises(ValidationError):
        RequestValidator.validate_input(['test', 123], schema)

def test_request_validator_sanitization():
    """Test input sanitization."""
    data = {
        'text': '<script>alert("xss")</script>',
        'nested': {
            'html': '<img src="malicious.jpg" onerror="evil()">'
        },
        'list': ['<p>test</p>']
    }
    
    sanitized = RequestValidator.sanitize_input(data)
    
    assert '<script>' not in sanitized['text']
    assert '<img' not in sanitized['nested']['html']
    assert '<p>' not in sanitized['list'][0]

def test_audit_logger_request_logging(audit_logger):
    """Test request logging."""
    with patch.object(audit_logger.logger, 'info') as mock_info:
        audit_logger.log_request(
            method='GET',
            path='/api/test',
            user='test_user',
            data={'key': 'value'}
        )
        
        mock_info.assert_called_once()
        args = mock_info.call_args[0]
        assert 'API Request' in args
        kwargs = mock_info.call_args[1]
        assert kwargs['method'] == 'GET'
        assert kwargs['path'] == '/api/test'
        assert kwargs['user'] == 'test_user'

def test_audit_logger_security_event(audit_logger):
    """Test security event logging."""
    with patch.object(audit_logger.logger, 'warning') as mock_warning:
        audit_logger.log_security_event(
            'authentication_failure',
            {'user': 'test_user', 'reason': 'invalid_token'}
        )
        
        mock_warning.assert_called_once()
        kwargs = mock_warning.call_args[1]
        assert kwargs['event_type'] == 'authentication_failure'
        assert kwargs['user'] == 'test_user'

def test_rate_limit_decorator():
    """Test rate limit decorator."""
    limiter = RateLimiter(2, 2)  # 2 tokens per second, 2 max
    
    @rate_limit(1)
    def test_function():
        return "success"
    
    with patch('src.core.security.rate_limiter', limiter):
        # First two calls should succeed
        assert test_function() == "success"
        assert test_function() == "success"
        
        # Third call should fail
        with pytest.raises(RateLimitError):
            test_function()

def test_validate_request_decorator():
    """Test request validation decorator."""
    schema = {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'}
        },
        'required': ['name']
    }
    
    @validate_request(schema)
    def test_function(data):
        return data
    
    # Valid request
    result = test_function(data={'name': 'test'})
    assert result['name'] == 'test'
    
    # Invalid request
    with pytest.raises(SecurityError):
        test_function(data={'name': 123})

def test_audit_log_decorator():
    """Test audit log decorator."""
    @audit_log('test_event')
    def test_function(arg):
        if arg == 'fail':
            raise ValueError("Test error")
        return "success"
    
    with patch('src.core.security.audit_logger') as mock_logger:
        # Successful execution
        test_function('success')
        mock_logger.log_security_event.assert_called_with(
            'test_event',
            {
                'status': 'success',
                'args': ('success',),
                'kwargs': {},
                'timestamp': mock_logger.log_security_event.call_args[0][1]['timestamp']
            }
        )
        
        # Failed execution
        with pytest.raises(ValueError):
            test_function('fail')
        mock_logger.log_security_event.assert_called_with(
            'test_event',
            {
                'status': 'error',
                'error': 'Test error',
                'args': ('fail',),
                'kwargs': {},
                'timestamp': mock_logger.log_security_event.call_args[0][1]['timestamp']
            }
        )

def test_concurrent_rate_limiting():
    """Test rate limiting under concurrent access."""
    import threading
    
    limiter = RateLimiter(10, 10)
    success_count = 0
    thread_count = 20
    
    def worker():
        nonlocal success_count
        if limiter.acquire():
            success_count += 1
    
    threads = [
        threading.Thread(target=worker)
        for _ in range(thread_count)
    ]
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
    
    assert success_count <= 10  # Should not exceed capacity

def test_request_validation_edge_cases():
    """Test request validation edge cases."""
    # Empty schema
    with pytest.raises(ValueError):
        RequestValidator.validate_input({}, {})
    
    # Invalid schema
    with pytest.raises(ValueError):
        RequestValidator.validate_input({}, {'properties': {}})
    
    # None values
    schema = {'type': 'object', 'properties': {'key': {'type': 'string'}}}
    with pytest.raises(ValidationError):
        RequestValidator.validate_input(None, schema)
    
    # Empty string
    RequestValidator.validate_input('', {'type': 'string'})  # Should not raise
    
    # Empty array
    RequestValidator.validate_input([], {'type': 'array'})  # Should not raise