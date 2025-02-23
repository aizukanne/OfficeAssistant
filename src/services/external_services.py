import os
import json
import random
import asyncio
import aiohttp
import requests
import logging
import re
from aiohttp.client_exceptions import ClientConnectorSSLError, ClientError
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError, RequestException
from typing import Optional, Tuple, Dict, Any, List
from urllib.parse import urlparse, quote_plus, urljoin

# User agents for rotating browser headers
USER_AGENTS = [
    # Chrome (Windows, macOS, Linux)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
    # Firefox (Windows, macOS, Linux)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:93.0) Gecko/20100101 Firefox/93.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",
    # Safari (macOS, iOS)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.1.2 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    # Edge (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.64",
    # Opera
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.277",
    # Mobile Browsers (Android, iOS)
    "Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Pixel 4 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1"
]

# Proxy configuration
proxy_url = "http://aizukanne3:Ng8qM7DCChitRRuGDusL_country-US,CA@core-residential.evomi.com:1000"

def make_request(url: str, method: str = 'GET', headers: Optional[Dict] = None, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict:
    """
    Utility function to make HTTP requests and handle errors.
    
    Args:
        url: The URL for the request
        method: The HTTP method ('GET', 'POST', etc.)
        headers: The headers for the request
        params: The query parameters for the request
        data: The data to send in the request body
    
    Returns:
        Dict: The JSON response or an error message
    """
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            return {'status': 'error', 'message': 'Invalid HTTP method'}

        response.raise_for_status()
        return response.json()
    except HTTPError as http_err:
        return {'status': 'error', 'message': f'HTTP error occurred: {http_err}'}
    except RequestException as req_err:
        return {'status': 'error', 'message': f'Request error occurred: {req_err}'}
    except Exception as err:
        return {'status': 'error', 'message': f'An error occurred: {err}'}

def clean_website_data(raw_text: str) -> str:
    """
    Cleans up raw website text data, removing common HTML artifacts and excess whitespace.
    """
    try:
        # Remove HTML tags (basic HTML tag removal)
        cleaned_text = re.sub('<[^<]+?>', '', raw_text)

        # Remove multiple spaces and newlines, and then trim
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        # Remove non-printing characters
        cleaned_text = ''.join(c for c in cleaned_text if c.isprintable())
        return cleaned_text

    except Exception as e:
        return json.dumps({"error": f"Error processing text: {str(e)}"})

async def fetch_page(session: aiohttp.ClientSession, url: str, timeout: int = 30) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetches a webpage with the given URL using an aiohttp session.
    """
    headers = {
        'User-Agent': random.choice(USER_AGENTS)
    }    
    try:
        async with session.get(url, headers=headers, proxy=proxy_url, timeout=timeout) as response:
            content_type = response.headers.get('Content-Type', '')
            if 'text' in content_type:
                encoding = response.charset or 'utf-8'
                return await response.text(encoding=encoding), content_type
            elif 'application/pdf' in content_type or 'application/msword' in content_type or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
                return await response.read(), content_type
            else:
                return None, content_type
    except asyncio.TimeoutError:
        print(f"Timeout error: {url} took too long to respond.")
        return f"Timeout error: {url} took too long to respond.", None
    except ClientConnectorSSLError:
        print(f"SSL handshake error: Failed to connect to {url}")
        return f"SSL handshake error: Failed to connect to {url}", None

async def process_page(session: aiohttp.ClientSession, url: str, semaphore: asyncio.Semaphore, full_text: bool = False) -> List[Dict]:
    """
    Processes a webpage, extracting and cleaning its content.
    """
    async with semaphore:
        try:
            result = await fetch_page(session, url)
        except ClientError as e:
            logging.error(f"Client error occurred while fetching the page: {e}")
            return [{
                "type": "text",
                "text": {
                    'url': url,
                    'error': 'Failed to fetch page due to client error'
                }
            }]
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")
            return [{
                "type": "text",
                "text": {
                    'url': url,
                    'error': 'An unexpected error occurred while fetching the page'
                }
            }]
        
        response_list = []

        try:
            if isinstance(result, tuple):
                document_content, content_type = result
                if document_content is not None and content_type is not None:
                    try:
                        s3_url = upload_document_to_s3(document_content, content_type, url)
                        response_list.append({
                            "type": "text",
                            "text": {
                                'url': url,
                                'summary': 'This file contains additional information for your search. Send it to the user.',
                                's3_url': s3_url
                            }
                        })
                    except Exception as e:
                        logging.error(f"Failed to upload document to S3: {e}")
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

                elements_to_extract = ['p', 'li', 'summary', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'pre', 'td', 'th', 'a']

                text = ' '.join(element.get_text().strip() for element in soup.find_all(elements_to_extract))
                cleaned_text = clean_website_data(text)

                if full_text:
                    summary_or_full_text = rank_sentences(cleaned_text, stopwords, max_sentences=150)
                else:
                    try:
                        summary_or_full_text = rank_sentences(cleaned_text, stopwords, max_sentences=50)
                    except Exception as e:
                        logging.error(f"Failed to rank sentences: {e}")
                        summary_or_full_text = cleaned_text  # Fallback to full text if ranking fails

                author = soup.find('meta', {'name': 'author'})['content'] if soup.find('meta', {'name': 'author'}) else 'Unknown'
                date_published = soup.find('meta', {'property': 'article:published_time'})['content'] if soup.find('meta', {'property': 'article:published_time'}) else 'Unknown'

                links = []

                response_list.append({
                    "type": "text",
                    "text": {
                        'summary_or_full_text': summary_or_full_text,
                        'author': author,
                        'date_published': date_published,
                        'internal_links': links
                    }
                })

                images = soup.select('article img') + soup.select('figure img') + soup.select('section img')
                
                for img in images:
                    img_url = img.get('src')
                    if img_url:
                        # Skip data URIs and other non-HTTP/HTTPS sources
                        if img_url.startswith('data:'):
                            continue
                        if not img_url.startswith(('http://', 'https://')):
                            img_url = urljoin(url, img_url)
                        
                        try:
                            async with session.head(img_url) as img_response:
                                if img_response.status == 200 and int(img_response.headers.get('Content-Length', 0)) > 10240:
                                    response_list.append({
                                        "type": "image_url",
                                        "image_url": {
                                            'url': img_url
                                        }
                                    })
                        except ClientError as e:
                            logging.error(f"Failed to fetch image: {img_url} - ClientError: {e}")
                        except Exception as e:
                            logging.error(f"Failed to fetch image: {img_url} - Unexpected error: {e}")
            else:
                response_list.append({
                    "type": "text",
                    "text": {
                        'url': url,
                        'error': result
                    }
                })
        except Exception as e:
            logging.error(f"Error processing page: {e}")
            response_list.append({
                "type": "text",
                "text": {
                    'url': url,
                    'error': 'An error occurred while processing the page'
                }
            })

        return response_list

async def get_web_pages(urls: List[str], full_text: bool = False, max_concurrent_requests: int = 5) -> List[Dict]:
    """
    Fetches and processes multiple web pages concurrently.
    """
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(max_concurrent_requests)
        tasks = [process_page(session, url, semaphore, full_text) for url in urls]
        results = await asyncio.gather(*tasks)
        
        # Flatten the list of results
        flattened_results = [item for sublist in results for item in sublist]
        print(json.dumps(flattened_results))
        
        return flattened_results

def google_search(search_term: str, before: Optional[str] = None, after: Optional[str] = None, 
                 intext: Optional[str] = None, allintext: Optional[str] = None, 
                 and_condition: Optional[str] = None, must_have: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs a Google search with advanced search operators.
    """
    custom_search_api_key = os.getenv('GOOGLE_API_KEY')
    custom_search_id = os.getenv('GOOGLE_SEARCH_CX')

    # Constructing the search term with advanced operators
    search_components = [search_term]

    if and_condition:
        search_components.append(search_term + " AND " + and_condition)

    if before:
        search_components.append(f"before:{before}")

    if after:
        search_components.append(f"after:{after}")

    if intext:
        search_components.append(f"intext:{intext}")
    
    if allintext:
        search_components.append(f"allintext:{allintext}")
    
    if must_have:
        search_components.append(f"\"{must_have}\"")

    combined_search_term = ' '.join(search_components)
    url_encoded_search_term = quote_plus(combined_search_term)
    print(f'Search Term: {url_encoded_search_term}')

    search_url = f"https://www.googleapis.com/customsearch/v1?q={url_encoded_search_term}&cx={custom_search_id}&key={custom_search_api_key}"
    response = requests.get(search_url)
    results = response.json().get('items', [])
    print(json.dumps(results))

    web_links = []
    for result in results:
        web_links.append(result['link'])
    
    web_content = asyncio.run(get_web_pages(web_links[:5]))
    print(json.dumps(web_content))
    
    return web_content

def browse_internet(urls: List[str], full_text: bool = False) -> List[Dict]:
    """
    Browses and extracts content from a list of URLs.
    """
    web_pages = asyncio.run(get_web_pages(urls, full_text))
    print(web_pages)
    return web_pages

def calendar_operations(access_token: str, calendar_id: str, operation: str, event_id: Optional[str] = None, event_data: Optional[Dict] = None) -> Dict:
    """
    Perform operations on Google Calendar.
    
    Args:
        access_token: Google OAuth access token
        calendar_id: ID of the calendar
        operation: Operation to perform ('read', 'create', 'update', 'delete')
        event_id: Optional ID of the event for update/delete operations
        event_data: Optional event data for create/update operations
        
    Returns:
        Dict: Operation result or error message
    """
    base_url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response_data = {}

    try:
        if operation == 'read':
            time_min = datetime.datetime.utcnow().isoformat() + 'Z'
            url = f"{base_url}/events?timeMin={time_min}"
            response_data = make_request(url, 'GET', headers=headers)

        elif operation == 'create':
            url = f"{base_url}/events"
            response_data = make_request(url, 'POST', headers=headers, data=event_data)

        elif operation == 'update':
            if event_id is None:
                raise ValueError("event_id is required for updating an event")
            url = f"{base_url}/events/{event_id}"
            response_data = make_request(url, 'PUT', headers=headers, data=event_data)

        elif operation == 'delete':
            if event_id is None:
                raise ValueError("event_id is required for deleting an event")
            url = f"{base_url}/events/{event_id}"
            response_data = make_request(url, 'DELETE', headers=headers)

        else:
            response_data['status'] = 'error'
            response_data['message'] = 'Invalid operation'

    except ValueError as ve:
        response_data['status'] = 'error'
        response_data['message'] = str(ve)

    return response_data

def exchange_auth_code_for_tokens(client_id: str, client_secret: str, authorization_code: str, redirect_uri: str) -> Dict:
    """
    Exchange authorization code for OAuth tokens.
    
    Args:
        client_id: OAuth client ID
        client_secret: OAuth client secret
        authorization_code: Authorization code to exchange
        redirect_uri: Redirect URI used in the OAuth flow
        
    Returns:
        Dict: OAuth tokens or error message
    """
    token_endpoint = 'https://oauth2.googleapis.com/token'
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': authorization_code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    return make_request(token_endpoint, 'POST', data=token_data)

def get_coordinates(location_name: str) -> Optional[Tuple[float, float]]:
    """
    Get geographical coordinates for a location.
    
    Args:
        location_name: Name of the location
        
    Returns:
        Optional[Tuple[float, float]]: Latitude and longitude if found
    """
    openweather_api_key = os.getenv('OPENWEATHER_KEY')
    base_url = 'http://api.openweathermap.org/geo/1.0/direct'
    params = {
        'q': location_name,
        'limit': 1,
        'appid': openweather_api_key
    }

    response = make_request(base_url, 'GET', params=params)
    if response.get('status') == 'error':
        return None

    data = response
    if data:
        lat = data[0]['lat']
        lon = data[0]['lon']
        return lat, lon
    return None

def get_weather_data(location_name: str = 'Whitehorse') -> Dict:
    """
    Get weather information for a location.
    
    Args:
        location_name: Name of the location (default: 'Whitehorse')
        
    Returns:
        Dict: Weather data or error message
    """
    openweather_api_key = os.getenv('OPENWEATHER_KEY')
    if not location_name.strip():
        return 'Location name is empty or contains only spaces. Please provide a valid location name.'

    coordinates = get_coordinates(location_name)
    if not coordinates:
        return 'Geolocation Failed! I could not find this location on a MAP.'

    lat, lon = coordinates
    url = 'https://api.openweathermap.org/data/3.0/onecall'
    params = {
        'appid': openweather_api_key,
        'lat': lat,
        'lon': lon,
        'exclude': 'hourly, minutely, daily',
        'units': 'metric'
    }

    response = make_request(url, 'GET', params=params)
    if response.get('status') == 'error':
        return f'Failed to get weather data: {response.get("message")}'

    return response