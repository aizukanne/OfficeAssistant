"""Authentication service package.

This package provides authentication functionality through
a clean, public interface while hiding implementation details.

Example:
    >>> from src.services.auth import authenticate
    >>> result = authenticate()
    >>> result['session_id']
    'abc123...'
"""
from .service import AuthService
from .functions import authenticate

__all__ = ['AuthService', 'authenticate']

# Version tracking
__version__ = '1.0.0'