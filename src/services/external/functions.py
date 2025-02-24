"""External service function wrappers."""
from typing import Dict, Any, List, Optional
from src.utils.logging import log_message, log_error
from src.utils.decorators import log_function_call
from src.utils.error_handling import handle_service_error, with_error_recovery
from src.core.exceptions import ServiceError
from .service import ExternalService

# Singleton instance
_instance: Optional[ExternalService] = None

def get_instance() -> ExternalService:
    """Get singleton instance."""
    global _instance
    if _instance is None:
        _instance = ExternalService()
    return _instance

__version__ = '1.0.0'

def get_version() -> str:
    """Get service version."""
    return __version__

@log_function_call('external')
@with_error_recovery(
    operation=lambda location: get_instance().search(f"coordinates of {location}"),
    recovery=lambda location: {"error": "Location not found"}
)
def get_coordinates(location: str) -> Dict[str, Any]:
    """
    Get coordinates for a location.
    
    Args:
        location: Name or address of location to find
    
    Returns:
        Dict[str, Any]: Location coordinates
            Contains:
            - lat (float): Latitude
            - lng (float): Longitude
            - address (str): Formatted address
    
    Raises:
        ServiceError: If coordinates cannot be found
            Context includes:
            - location: Original location string
            - error: Error details
    
    Example:
        >>> coords = get_coordinates("San Francisco")
        >>> coords["lat"]
        37.7749
    """
    try:
        service = get_instance()
        return service.search(f"coordinates of {location}")
    except Exception as e:
        handle_service_error(
            'external',
            'get_coordinates',
            ServiceError,
            location=location
        )(e)

@log_function_call('external')
@with_error_recovery(
    operation=lambda location: get_instance().search(f"weather in {location}"),
    recovery=lambda location: {"error": "Weather data unavailable"}
)
def get_weather_data(location: str) -> Dict[str, Any]:
    """
    Get weather data for a location.
    
    Args:
        location: Name or address of location
    
    Returns:
        Dict[str, Any]: Weather information
            Contains:
            - temperature (float): Current temperature
            - conditions (str): Weather conditions
            - humidity (int): Humidity percentage
            - wind_speed (float): Wind speed
    
    Raises:
        ServiceError: If weather data cannot be retrieved
            Context includes:
            - location: Original location string
            - error: Error details
    
    Example:
        >>> weather = get_weather_data("London")
        >>> weather["temperature"]
        20.5
    """
    try:
        service = get_instance()
        return service.search(f"weather in {location}")
    except Exception as e:
        handle_service_error(
            'external',
            'get_weather_data',
            ServiceError,
            location=location
        )(e)

@log_function_call('external')
@with_error_recovery(
    operation=lambda query, **kwargs: get_instance().search(query, **kwargs),
    recovery=lambda query, **kwargs: [{"error": "Search failed"}]
)
def browse_internet(query: str, **kwargs: Any) -> List[Dict[str, Any]]:
    """
    Browse internet for information.
    
    Args:
        query: Search query
        **kwargs: Additional search parameters
            - full_text (bool): Whether to return full text
            - max_results (int): Maximum number of results
    
    Returns:
        List[Dict[str, Any]]: Search results
            Each dict contains:
            - title (str): Result title
            - url (str): Result URL
            - summary (str): Result summary
    
    Raises:
        ServiceError: If search fails
            Context includes:
            - query: Original search query
            - error: Error details
    
    Example:
        >>> results = browse_internet("Python programming")
        >>> results[0]["title"]
        'Python Programming Language'
    """
    try:
        service = get_instance()
        return service.search(query, **kwargs)
    except Exception as e:
        handle_service_error(
            'external',
            'browse_internet',
            ServiceError,
            query=query,
            **kwargs
        )(e)

@log_function_call('external')
@with_error_recovery(
    operation=lambda query, **kwargs: get_instance().search(query, **kwargs),
    recovery=lambda query, **kwargs: [{"error": "Search failed"}]
)
def google_search(query: str, **kwargs: Any) -> List[Dict[str, Any]]:
    """
    Perform a Google search.
    
    Args:
        query: Search query
        **kwargs: Additional search parameters
            - and_condition (str): AND condition
            - before (str): Date before
            - after (str): Date after
            - intext (str): Text to find
            - allintext (str): All text to find
            - must_have (str): Required text
    
    Returns:
        List[Dict[str, Any]]: Search results
            Each dict contains:
            - title (str): Result title
            - url (str): Result URL
            - snippet (str): Result snippet
    
    Raises:
        ServiceError: If search fails
            Context includes:
            - query: Original search query
            - error: Error details
    
    Example:
        >>> results = google_search("Python tutorial")
        >>> results[0]["title"]
        'Python Tutorial - W3Schools'
    """
    try:
        service = get_instance()
        return service.search(query, **kwargs)
    except Exception as e:
        handle_service_error(
            'external',
            'google_search',
            ServiceError,
            query=query,
            **kwargs
        )(e)