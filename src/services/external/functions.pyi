"""Type hints for external service functions."""
from typing import Dict, Any, List, Optional
from .service import ExternalService

def get_instance() -> ExternalService: ...

def get_version() -> str: ...

def get_coordinates(location: str) -> Dict[str, Any]: ...

def get_weather_data(location: str) -> Dict[str, Any]: ...

def browse_internet(
    query: str,
    *,
    full_text: Optional[bool] = None,
    max_results: Optional[int] = None,
    **kwargs: Any
) -> List[Dict[str, Any]]: ...

def google_search(
    query: str,
    *,
    and_condition: Optional[str] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    intext: Optional[str] = None,
    allintext: Optional[str] = None,
    must_have: Optional[str] = None,
    **kwargs: Any
) -> List[Dict[str, Any]]: ...