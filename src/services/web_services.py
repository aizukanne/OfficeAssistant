import asyncio
import json
import random
import logging
import requests
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, quote_plus
from aiohttp.client_exceptions import ClientConnectorSSLError
from botocore.exceptions import ClientError

from ..core.config import (
    PROXY_URL,
    USER_AGENTS,
    GOOGLE_API_KEY,
    DOCS_BUCKET_NAME
)
from ..core.error_handlers import decimal_default

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def browse_internet(urls: List[str], full_text: bool = False) -> List[Dict[str, Any]]:
    """
    Browse multiple URLs and extract content.

    Args:
        urls: List of URLs to browse
        full_text: Whether to return full text or summary

    Returns:
        List of dictionaries containing web page content
    """
    web_pages = await get_web_pages(urls, full_text)
    logger.info(f"Retrieved content from {len(web_pages)} pages")
    return web_pages

def google_search(
    search_term: str,
    before: Optional[str] = None,
    after: Optional[str] = None,
    intext: Optional[str] = None,
    allintext: Optional[str] = None,
    and_condition: Optional[str] = None,
    must_have: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Perform a Google search with advanced operators.

    Args:
        search_term: Main search term
        before: Date filter (YYYY-MM-DD)
        after: Date filter (YYYY-MM-DD)
        intext: Text that should appear in the content
        allintext: All terms that should appear in the content
        and_condition: Additional AND condition
        must_have: Exact phrase match

    Returns:
        List of search results with extracted content
    """
    # Constructing the search term with advanced operators
    search_components = [search_term]

    if and_condition:
        search_components.append(f"{search_term} AND {and_condition}")
    if before:
        search_components.append(f"before:{before}")
    if after:
        search_components.append(f"after:{after}")
    if intext:
        search_components.append(f"intext:{intext}")
    if allintext:
        search_components.append(f"allintext:{allintext}")
    if must_have:
        search_components.append(f'"{must_have}"')

    # Join components and encode for URL
    combined_search_term = ' '.join(search_components)
    url_encoded_search_term = quote_plus(combined_search_term)
    logger.info(f'Search Term: {url_encoded_search_term}')

    # Build and execute search request
    search_url = (
        f"https://www.googleapis.com/customsearch/v1"
        f"?q={url_encoded_search_term}"
        f"&cx={CUSTOM_SEARCH_ID}"
        f"&key={GOOGLE_API_KEY}"
    )
    
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        results = response.json().get('items', [])
        
        web_links = [result['link'] for result in results]
        web_content = asyncio.run(get_web_pages(web_links[:5]))
        
        return web_content
    except requests.exceptions.RequestException as e:
        logger.error(f"Error performing Google search: {e}")
        return []

async def get_web_pages(
    urls: List[str],
    full_text: bool = False,
    max_concurrent_requests: int = 5
) -> List[Dict[str, Any]]:
    """
    Fetch and process multiple web pages concurrently.

    Args:
        urls: List of URLs to fetch
        full_text: Whether to return full text or summary
        max_concurrent_requests: Maximum concurrent requests

    Returns:
        List of processed web page content
    """
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(max_concurrent_requests)
        tasks = [
            process_page(session, url, semaphore, full_text)
            for url in urls
        ]
        results = await asyncio.gather(*tasks)
        
        # Flatten the list of results
        flattened_results = [
            item for sublist in results
            for item in sublist
        ]
        
        return flattened_results

async def fetch_page(
    session: aiohttp.ClientSession,
    url: str,
    timeout: int = 30
) -> tuple[Optional[str], Optional[str]]:
    """
    Fetch a single web page.

    Args:
        session: aiohttp ClientSession
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Tuple of (content, content_type)
    """
    headers = {
        'User-Agent': random.choice(USER_AGENTS)
    }
    
    try:
        async with session.get(
            url,
            headers=headers,
            proxy=PROXY_URL,
            timeout=timeout
        ) as response:
            content_type = response.headers.get('Content-Type', '')
            
            if 'text' in content_type:
                encoding = response.charset or 'utf-8'
                return await response.text(encoding=encoding), content_type
            elif any(t in content_type for t in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']):
                return await response.read(), content_type
            else:
                return None, content_type
    except asyncio.TimeoutError:
        logger.error(f"Timeout error: {url} took too long to respond.")
        return f"Timeout error: {url} took too long to respond.", None
    except ClientConnectorSSLError:
        logger.error(f"SSL handshake error: Failed to connect to {url}")
        return f"SSL handshake error: Failed to connect to {url}", None

async def process_page(
    session: aiohttp.ClientSession,
    url: str,
    semaphore: asyncio.Semaphore,
    full_text: bool = False
) -> List[Dict[str, Any]]:
    """
    Process a web page and extract its content.

    Args:
        session: aiohttp ClientSession
        url: URL to process
        semaphore: Semaphore for rate limiting
        full_text: Whether to return full text or summary

    Returns:
        List of content items (text and images)
    """
    async with semaphore:
        try:
            result = await fetch_page(session, url)
            response_list = []

            if isinstance(result, tuple):
                document_content, content_type = result
                if document_content is not None and content_type is not None:
                    try:
                        s3_url = upload_document_to_s3(document_content, content_type, url)
                        response_list.append({
                            "type": "text",
                            "text": {
                                'url': url,
                                'summary': 'This file contains additional information for your search.',
                                's3_url': s3_url
                            }
                        })
                    except Exception as e:
                        logger.error(f"Failed to upload document to S3: {e}")
                        response_list.append({
                            "type": "text",
                            "text": {
                                'url': url,
                                'error': 'Failed to upload document to S3'
                            }
                        })
                else:
                    response_list.append({
                        "type": "text",
                        "text": {
                            'url': url,
                            'error': 'Unsupported content type'
                        }
                    })
            elif isinstance(result, str) and 'Timeout error' not in result:
                soup = BeautifulSoup(result, 'lxml')
                
                # Extract text content
                elements_to_extract = [
                    'p', 'li', 'summary', 'div', 'span', 'h1', 'h2', 'h3',
                    'h4', 'h5', 'h6', 'blockquote', 'pre', 'td', 'th', 'a'
                ]
                text = ' '.join(
                    element.get_text().strip()
                    for element in soup.find_all(elements_to_extract)
                )
                cleaned_text = clean_website_data(text)  # This needs to be imported from message_processing

                # Process text based on full_text flag
                if full_text:
                    summary_or_full_text = rank_sentences(cleaned_text, stopwords, max_sentences=150)
                else:
                    try:
                        summary_or_full_text = rank_sentences(cleaned_text, stopwords, max_sentences=50)
                    except Exception as e:
                        logger.error(f"Failed to rank sentences: {e}")
                        summary_or_full_text = cleaned_text

                # Extract metadata
                author = (
                    soup.find('meta', {'name': 'author'})['content']
                    if soup.find('meta', {'name': 'author'})
                    else 'Unknown'
                )
                date_published = (
                    soup.find('meta', {'property': 'article:published_time'})['content']
                    if soup.find('meta', {'property': 'article:published_time'})
                    else 'Unknown'
                )

                response_list.append({
                    "type": "text",
                    "text": {
                        'summary_or_full_text': summary_or_full_text,
                        'author': author,
                        'date_published': date_published,
                        'internal_links': []
                    }
                })

                # Extract images
                images = (
                    soup.select('article img') +
                    soup.select('figure img') +
                    soup.select('section img')
                )
                
                for img in images:
                    img_url = img.get('src')
                    if img_url:
                        if img_url.startswith('data:'):
                            continue
                        if not img_url.startswith(('http://', 'https://')):
                            img_url = urljoin(url, img_url)
                        
                        try:
                            async with session.head(img_url) as img_response:
                                if (
                                    img_response.status == 200 and
                                    int(img_response.headers.get('Content-Length', 0)) > 10240
                                ):
                                    response_list.append({
                                        "type": "image_url",
                                        "image_url": {'url': img_url}
                                    })
                        except Exception as e:
                            logger.error(f"Failed to fetch image: {img_url} - {e}")
            else:
                response_list.append({
                    "type": "text",
                    "text": {
                        'url': url,
                        'error': result
                    }
                })

            return response_list

        except Exception as e:
            logger.error(f"Error processing page: {e}")
            return [{
                "type": "text",
                "text": {
                    'url': url,
                    'error': 'An error occurred while processing the page'
                }
            }]

def upload_document_to_s3(
    document_content: bytes,
    content_type: str,
    document_url: str
) -> str:
    """
    Upload a document to S3.

    Args:
        document_content: Raw document content
        content_type: MIME type of the document
        document_url: Original URL of the document

    Returns:
        S3 URL of the uploaded document
    """
    try:
        document_extension = mimetypes.guess_extension(content_type) or '.bin'
        s3_object_name = f"Document_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{document_extension}"

        s3_client = boto3.client('s3')
        s3_client.put_object(
            Body=document_content,
            Bucket=DOCS_BUCKET_NAME,
            Key=s3_object_name
        )

        s3_url = f"https://{DOCS_BUCKET_NAME}.s3.amazonaws.com/{s3_object_name}"
        return s3_url
    except Exception as e:
        logger.error(f"Failed to upload document to S3: {e}")
        raise