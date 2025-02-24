"""Authentication service implementation.

Provides functionality for:
- User authentication
- Session management
- Token validation
- Access control

Configuration:
- Requires valid Odoo credentials
- Environment variables must be set
- Network access needed

Example:
    >>> service = AuthService()
    >>> result = service.authenticate()
    >>> result['session_id']
    'abc123...'
"""
import os
import requests
from typing import Dict, Any, Optional

from src.utils.logging import log_message, log_error
from src.utils.decorators import log_function_call
from src.utils.error_handling import handle_service_error
from src.core.exceptions import (
    AuthenticationError,
    ValidationError,
    ConfigurationError,
    NetworkError
)
from src.interfaces import ServiceInterface
from src.config.settings import ODOO_CONFIG

__version__ = '1.0.0'

@log_function_call('auth')
class AuthService(ServiceInterface):
    """Authentication service implementation.
    
    Handles user authentication and session management.
    
    Attributes:
        session_id: Optional[str]
            Current session ID if authenticated
    
    Example:
        >>> auth = AuthService()
        >>> auth.initialize()
        >>> auth.authenticate()
        {'session_id': 'abc123...'}
    """
    
    def __init__(self) -> None:
        """Initialize the service."""
        self.session_id: Optional[str] = None
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize authentication service."""
        try:
            self.validate_config()
            log_message('INFO', 'auth', 'Service initialized')
        except Exception as e:
            handle_service_error(
                'auth',
                'initialize',
                ConfigurationError,
                config_exists=bool(ODOO_CONFIG)
            )(e)
    
    def validate_config(self) -> Dict[str, str]:
        """Validate service configuration."""
        missing = {}
        
        if not ODOO_CONFIG['url']:
            missing['ODOO_URL'] = "Odoo URL is required"
            log_message('ERROR', 'auth', 'Missing Odoo URL')
        if not ODOO_CONFIG['db']:
            missing['ODOO_DB'] = "Odoo database name is required"
            log_message('ERROR', 'auth', 'Missing Odoo database')
        if not ODOO_CONFIG['username']:
            missing['ODOO_USERNAME'] = "Odoo username is required"
            log_message('ERROR', 'auth', 'Missing Odoo username')
        if not ODOO_CONFIG['password']:
            missing['ODOO_PASSWORD'] = "Odoo password is required"
            log_message('ERROR', 'auth', 'Missing Odoo password')
            
        return missing

    @log_function_call('auth')
    @handle_service_error('auth', 'authenticate', AuthenticationError)
    def authenticate(self) -> Dict[str, str]:
        """
        Authenticate with Odoo and get session cookie.
        
        Returns:
            Dict[str, str]: Authentication result containing:
                - session_id: Session cookie value
                
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
        """
        try:
            # Validate configuration
            if missing := self.validate_config():
                raise ConfigurationError(
                    "Missing configuration values",
                    missing=missing
                )
            
            # Prepare request
            endpoint = f"{ODOO_CONFIG['url']}/web/session/authenticate"
            headers = {'Content-Type': 'application/json'}
            payload = {
                "params": {
                    "db": ODOO_CONFIG['db'],
                    "login": ODOO_CONFIG['username'],
                    "password": ODOO_CONFIG['password']
                }
            }
            
            log_message('INFO', 'auth', 'Authenticating with Odoo',
                       url=endpoint)
            
            # Make request
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            
            # Extract session ID
            session_id = response.cookies.get('session_id')
            if not session_id:
                raise AuthenticationError(
                    "Authentication failed",
                    reason="No session ID returned"
                )
            
            self.session_id = session_id
            log_message('INFO', 'auth', 'Authentication successful')
            return {'session_id': session_id}
            
        except requests.exceptions.HTTPError as e:
            raise AuthenticationError(
                "Authentication failed",
                status_code=e.response.status_code if e.response else None,
                error_response=e.response.text if e.response else None
            ) from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(
                "Network error during authentication",
                error_type=type(e).__name__,
                error_details=str(e)
            ) from e
            
    def get_session(self) -> Optional[str]:
        """
        Get current session ID if authenticated.
        
        Returns:
            Optional[str]: Session ID if authenticated, None otherwise
        """
        return self.session_id

# Singleton instance
_instance: Optional[AuthService] = None

def get_instance() -> AuthService:
    """Get singleton AuthService instance."""
    global _instance
    if _instance is None:
        _instance = AuthService()
    return _instance