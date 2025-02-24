"""Public authentication functions.

This module provides the public interface for authentication
functionality. All functions use the singleton AuthService
instance internally.

Example:
    >>> result = authenticate()
    >>> result['session_id']
    'abc123...'
"""
from typing import Dict, Any
from .service import get_instance
from src.utils.logging import log_message, log_error
from src.utils.decorators import log_function_call
from src.utils.error_handling import handle_service_error
from src.core.exceptions import AuthenticationError

@log_function_call('auth')
def authenticate() -> Dict[str, str]:
    """
    Authenticate user and get session.
    
    Returns:
        Dict[str, str]: Authentication result
            - session_id: Session identifier
            
    Raises:
        AuthenticationError: If authentication fails
            Context includes:
            - attempt_count: Number of attempts
            - error_details: Specific error info
        ConfigurationError: If credentials missing
            Context includes:
            - missing_vars: List of missing variables
        NetworkError: If service unavailable
            Context includes:
            - service_url: Attempted URL
            - error_code: HTTP status code
            
    Example:
        >>> result = authenticate()
        >>> isinstance(result['session_id'], str)
        True
    """
    try:
        return get_instance().authenticate()
    except Exception as e:
        handle_service_error(
            'auth',
            'authenticate',
            AuthenticationError,
            operation='authenticate'
        )(e)