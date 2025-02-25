import time
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional
from .error_handlers import APIError, format_error_response
from .config import SLACK_BOT_TOKEN

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiting implementation using token bucket algorithm"""
    def __init__(self, tokens: int, refill_rate: float):
        self.tokens = tokens  # Maximum tokens
        self.refill_rate = refill_rate  # Tokens per second
        self.current_tokens = tokens  # Current token count
        self.last_update = time.time()  # Last update timestamp

    def acquire(self) -> bool:
        """Attempt to acquire a token"""
        now = time.time()
        # Refill tokens based on time elapsed
        elapsed = now - self.last_update
        self.current_tokens = min(
            self.tokens,
            self.current_tokens + elapsed * self.refill_rate
        )
        self.last_update = now

        if self.current_tokens >= 1:
            self.current_tokens -= 1
            return True
        return False

# Global rate limiters
api_rate_limiter = RateLimiter(tokens=100, refill_rate=10)  # 100 requests per 10 seconds
slack_rate_limiter = RateLimiter(tokens=50, refill_rate=1)  # 50 requests per second

def validate_slack_event(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Validate incoming Slack event"""
    if 'event' not in event:
        return format_error_response(APIError(
            message="Invalid event format",
            status_code=400,
            details={"error": "Missing event data"}
        ))

    event_data = event['event']
    
    # Validate required fields
    required_fields = ['type', 'channel']
    missing_fields = [field for field in required_fields if field not in event_data]
    if missing_fields:
        return format_error_response(APIError(
            message="Missing required fields",
            status_code=400,
            details={"missing_fields": missing_fields}
        ))

    return None

def rate_limit(limiter: RateLimiter):
    """Rate limiting decorator"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not limiter.acquire():
                return format_error_response(APIError(
                    message="Rate limit exceeded",
                    status_code=429
                ))
            return func(*args, **kwargs)
        return wrapper
    return decorator

def log_execution_time(func: Callable) -> Callable:
    """Decorator to log function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
        return result
    return wrapper

def validate_request(func: Callable) -> Callable:
    """Decorator to validate incoming requests"""
    @wraps(func)
    def wrapper(event: Dict[str, Any], *args, **kwargs):
        # Validate event format
        validation_error = validate_slack_event(event)
        if validation_error:
            return validation_error

        # Check for bot messages to prevent loops
        if 'event' in event and 'bot_id' in event['event']:
            return {
                'statusCode': 200,
                'body': {'message': 'Ignored bot message'}
            }

        return func(event, *args, **kwargs)
    return wrapper

def authenticate_slack(func: Callable) -> Callable:
    """Decorator to authenticate Slack requests"""
    @wraps(func)
    def wrapper(event: Dict[str, Any], *args, **kwargs):
        # Verify Slack token
        if not SLACK_BOT_TOKEN:
            return format_error_response(APIError(
                message="Slack token not configured",
                status_code=401
            ))

        return func(event, *args, **kwargs)
    return wrapper

def handle_errors(func: Callable) -> Callable:
    """Decorator to handle errors and provide consistent error responses"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            return format_error_response(APIError(
                message="Internal server error",
                status_code=500,
                details={"error": str(e)}
            ))
    return wrapper

def compose_middleware(*decorators: Callable) -> Callable:
    """Compose multiple middleware decorators"""
    def decorator(func: Callable) -> Callable:
        for decorator in reversed(decorators):
            func = decorator(func)
        return func
    return decorator

# Standard middleware stack for lambda handlers
lambda_middleware = compose_middleware(
    handle_errors,
    authenticate_slack,
    validate_request,
    rate_limit(api_rate_limiter),
    log_execution_time
)

# Middleware stack for Slack API calls
slack_middleware = compose_middleware(
    handle_errors,
    rate_limit(slack_rate_limiter),
    log_execution_time
)

# Example usage:
# @lambda_middleware
# def lambda_handler(event, context):
#     # Handler implementation
#     pass