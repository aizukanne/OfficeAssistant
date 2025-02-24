"""External services implementation."""
import os
import json
import random
import asyncio
import aiohttp
import requests
import re
import datetime
import time
from aiohttp.client_exceptions import ClientConnectorSSLError, ClientError
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError, RequestException
from typing import Optional, Tuple, Dict, Any, List
from urllib.parse import quote_plus

from src.config.settings import (
    get_proxy_url,
    get_user_agent,
    get_api_endpoint,
    HTTP_CONFIG
)
from src.core.exceptions import (
    APIError,
    NetworkError,
    TimeoutError,
    ValidationError,
    ConfigurationError
)
from src.core.logging import ServiceLogger, log_function_call, log_error
from src.utils.text_processing import clean_text, rank_sentences, load_stopwords
from src.interfaces import ExternalServiceInterface
from src.services.storage import get_instance as get_storage_instance

# Initialize logger at module level
logger = ServiceLogger('external_services')

class ExternalService(ExternalServiceInterface):
    """Implementation of external service interface."""
    
    def __init__(self) -> None:
        """Initialize the service."""
        self.logger = ServiceLogger('external_services')
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize service configuration."""
        self.proxy_url = get_proxy_url()
        self.stopwords = load_stopwords()
        self.timeout = HTTP_CONFIG['timeout']
        self.max_retries = HTTP_CONFIG['max_retries']
        self.retry_delay = HTTP_CONFIG['retry_delay']
    
    def validate_config(self) -> Dict[str, str]:
        """Validate service configuration."""
        missing = {}
        
        if not os.getenv('GOOGLE_API_KEY'):
            missing['GOOGLE_API_KEY'] = "Google API key is required"
        if not os.getenv('GOOGLE_SEARCH_CX'):
            missing['GOOGLE_SEARCH_CX'] = "Google Search CX is required"
            
        return missing

    @log_function_call(logger)
    @log_error(logger)
    def make_request(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict:
        """Make an HTTP request with retries."""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                if method == 'GET':
                    response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
                elif method == 'POST':
                    response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
                elif method == 'PUT':
                    response = requests.put(url, headers=headers, json=data, timeout=self.timeout)
                elif method == 'DELETE':
                    response = requests.delete(url, headers=headers, timeout=self.timeout)
                else:
                    raise ValidationError(f"Invalid HTTP method: {method}")

                response.raise_for_status()
                return response.json()
                
            except HTTPError as http_err:
                self.logger.error(f"HTTP error occurred: {http_err}")
                if retry_count == self.max_retries - 1:
                    raise APIError(f"HTTP error occurred: {http_err}")
            except RequestException as req_err:
                self.logger.error(f"Request error occurred: {req_err}")
                if retry_count == self.max_retries - 1:
                    raise NetworkError(f"Request error occurred: {req_err}")
            except Exception as err:
                self.logger.error(f"An error occurred: {err}")
                if retry_count == self.max_retries - 1:
                    raise
                
            retry_count += 1
            time.sleep(self.retry_delay)  # Use synchronous sleep instead of async

    @log_function_call(logger)
    @log_error(logger)
    async def fetch_content(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Fetch content from a URL."""
        headers = {'User-Agent': get_user_agent()}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, proxy=self.proxy_url, timeout=self.timeout) as response:
                    content_type = response.headers.get('Content-Type', '')
                    if 'text' in content_type:
                        encoding = response.charset or 'utf-8'
                        return await response.text(encoding=encoding), content_type
                    elif 'application/pdf' in content_type or 'application/msword' in content_type:
                        return await response.read(), content_type
                    else:
                        return None, content_type
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout error: {url}")
            raise TimeoutError(f"Request to {url} timed out")
        except ClientConnectorSSLError:
            self.logger.error(f"SSL handshake error: {url}")
            raise NetworkError(f"SSL handshake failed for {url}")

    @log_function_call(logger)
    @log_error(logger)
    async def process_content(
        self,
        content: str,
        content_type: str,
        full_text: bool = False
    ) -> List[Dict[str, Any]]:
        """Process fetched content."""
        response_list = []

        try:
            if 'text/html' in content_type:
                soup = BeautifulSoup(content, 'lxml')
                elements = ['p', 'li', 'summary', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
                text = ' '.join(element.get_text().strip() for element in soup.find_all(elements))
                cleaned_text = clean_text(text)

                if full_text:
                    summary = rank_sentences(cleaned_text, self.stopwords, max_sentences=150)
                else:
                    summary = rank_sentences(cleaned_text, self.stopwords, max_sentences=50)

                response_list.append({
                    "type": "text",
                    "text": {
                        'summary': summary,
                        'author': soup.find('meta', {'name': 'author'})['content'] if soup.find('meta', {'name': 'author'}) else 'Unknown',
                        'date': soup.find('meta', {'property': 'article:published_time'})['content'] if soup.find('meta', {'property': 'article:published_time'}) else 'Unknown'
                    }
                })
            elif 'application/pdf' in content_type or 'application/msword' in content_type:
                storage = get_storage_instance()
                s3_url = storage.upload_to_s3('documents', content, file_key=f"{int(time.time())}.{content_type.split('/')[-1]}", content_type=content_type)
                response_list.append({
                    "type": "text",
                    "text": {
                        'summary': 'Document available for download',
                        's3_url': s3_url
                    }
                })

        except Exception as e:
            self.logger.error(f"Error processing content: {e}")
            response_list.append({
                "type": "text",
                "text": {
                    'error': str(e)
                }
            })

        return response_list

    @log_function_call(logger)
    @log_error(logger)
    def search(
        self,
        query: str,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Perform a search query."""
        search_components = [query]
        
        if kwargs.get('and_condition'):
            search_components.append(f"{query} AND {kwargs['and_condition']}")
        if kwargs.get('before'):
            search_components.append(f"before:{kwargs['before']}")
        if kwargs.get('after'):
            search_components.append(f"after:{kwargs['after']}")
        if kwargs.get('intext'):
            search_components.append(f"intext:{kwargs['intext']}")
        if kwargs.get('allintext'):
            search_components.append(f"allintext:{kwargs['allintext']}")
        if kwargs.get('must_have'):
            search_components.append(f"\"{kwargs['must_have']}\"")

        search_query = ' '.join(search_components)
        encoded_query = quote_plus(search_query)
        
        search_url = get_api_endpoint('google', 'search')
        response = self.make_request(search_url, params={'q': encoded_query})
        
        if response.get('status') == 'error':
            raise APIError(f"Google search failed: {response.get('message')}")
            
        results = response.get('items', [])
        web_links = [result['link'] for result in results]
        
        return asyncio.run(self._process_urls(web_links[:5], kwargs.get('full_text', False)))

    async def _process_urls(
        self,
        urls: List[str],
        full_text: bool = False
    ) -> List[Dict[str, Any]]:
        """Process multiple URLs concurrently."""
        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(HTTP_CONFIG['max_concurrent_requests'])
            tasks = []
            
            for url in urls:
                task = asyncio.create_task(self._process_single_url(
                    session, url, semaphore, full_text
                ))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            return [item for sublist in results for item in sublist]

    async def _process_single_url(
        self,
        session: aiohttp.ClientSession,
        url: str,
        semaphore: asyncio.Semaphore,
        full_text: bool
    ) -> List[Dict[str, Any]]:
        """Process a single URL."""
        async with semaphore:
            try:
                content, content_type = await self.fetch_content(url)
                if content is None:
                    return [{
                        "type": "text",
                        "text": {
                            'url': url,
                            'error': 'Failed to fetch content'
                        }
                    }]
                return await self.process_content(content, content_type, full_text)
            except Exception as e:
                self.logger.error(f"Error processing URL {url}: {e}")
                return [{
                    "type": "text",
                    "text": {
                        'url': url,
                        'error': str(e)
                    }
                }]