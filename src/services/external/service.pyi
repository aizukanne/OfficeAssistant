"""Type stubs for external service."""
from typing import Dict, List, Any, Optional, Tuple
import aiohttp
from src.interfaces import ExternalServiceInterface

class ExternalService(ExternalServiceInterface):
    """External service type hints."""
    
    proxy_url: str
    stopwords: List[str]
    timeout: float
    max_retries: int
    retry_delay: float
    
    def __init__(self) -> None: ...
    
    def initialize(self) -> None: ...
    
    def validate_config(self) -> Dict[str, str]: ...
    
    def make_request(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict: ...
    
    async def fetch_content(
        self,
        url: str
    ) -> Tuple[Optional[str], Optional[str]]: ...
    
    async def process_content(
        self,
        content: str,
        content_type: str,
        full_text: bool = False
    ) -> List[Dict[str, Any]]: ...
    
    def search(
        self,
        query: str,
        **kwargs: Any
    ) -> List[Dict[str, Any]]: ...
    
    async def _process_urls(
        self,
        urls: List[str],
        full_text: bool = False
    ) -> List[Dict[str, Any]]: ...
    
    async def _process_single_url(
        self,
        session: aiohttp.ClientSession,
        url: str,
        semaphore: aiohttp.Semaphore,
        full_text: bool
    ) -> List[Dict[str, Any]]: ...