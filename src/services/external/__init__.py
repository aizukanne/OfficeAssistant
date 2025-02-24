"""External services package."""
from .service import ExternalService
from .functions import (
    get_coordinates,
    get_weather_data,
    browse_internet,
    google_search,
    get_version
)

__version__ = get_version()

__all__ = [
    'ExternalService',
    'get_coordinates',
    'get_weather_data',
    'browse_internet',
    'google_search',
    '__version__'
]