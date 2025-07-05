"""
All Functions Module
====================

This module contains all the functions used in the Office Assistant application.
"""

# Import statements
import os
import json
import time
import boto3
import requests
import asyncio
import aiohttp
import datetime
import textwrap
import markdown2
import urllib.parse
import urllib.request
import logging
from decimal import Decimal
from urllib.parse import quote_plus
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from fpdf import FPDF
import weaviate
from weaviate.classes.query import Filter
import openai
from typing import Dict, List, Optional, Union, Any

# Import additional modules for web scraping and processing
import random
import mimetypes
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from aiohttp import ClientError, ClientConnectorSSLError
import tempfile
from nltk.tokenize import sent_tokenize, word_tokenize
import re

# Import from local modules
from config import (
    odoo_url, odoo_db, odoo_login, odoo_password, base_url,
    docs_bucket_name, gemini_api_key, client,
    names_table, channels_table, weaviate_client,
    slack_bot_token, image_bucket_name, proxy_url, USER_AGENTS
)
from url_shortener import URLShortener

# Constants
stopwords = set()  # Will be loaded by load_stopwords function


# Helper functions
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def is_serializable(value):
    """Helper function to check if a value is serializable."""
    try:
        json.dumps(value)
        return True
    except (TypeError, OverflowError):
        return False

def transform_objects(objects, collection_name):
    """Transform Weaviate objects to the expected format"""
    transformed = []
    for obj in objects:
        properties = obj.properties
        # Convert timestamp to Unix timestamp for sorting
        timestamp = properties.get('timestamp')
        if timestamp:
            # Parse ISO format timestamp and convert to Unix timestamp
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            sort_key = int(dt.timestamp())
        else:
            sort_key = 0
            
        transformed.append({
            "role": "user" if collection_name == "UserMessages" else "assistant",
            "message": properties.get('message', ''),
            "sort_key": sort_key,
            "chat_id": properties.get('chat_id', '')
        })
    return transformed

def replace_problematic_chars(text):
    """Replace problematic characters for PDF generation"""
    replacements = {
        '\u2018': "'",  # Left single quotation mark
        '\u2019': "'",  # Right single quotation mark
        '\u201C': '"',  # Left double quotation mark
        '\u201D': '"',  # Right double quotation mark
        '\u2013': '-',  # En dash
        '\u2014': '--', # Em dash
        '\u2026': '...', # Horizontal ellipsis
        '\u00A0': ' ',  # Non-breaking space
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def to_markdown(text):
    text = text.replace('•', '  *')
    indented_text = textwrap.indent(text, '> ', predicate=lambda _: True)
    html = markdown2.markdown(indented_text)
    return html

class MyFPDF(FPDF):
    def __init__(self, title):
        super().__init__()
        self.title = title

    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, self.title, 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')


# Helper functions for NLP and text processing
def load_stopwords(file_path):
    """
    Load stopwords from a given file.

    :param file_path: Path to the stopwords file.
    :return: Set of stopwords.
    """
    try:
        with open(file_path, 'r') as file:
            stopwords = set(file.read().splitlines())
        return stopwords
    except FileNotFoundError:
        # Return empty set if file not found
        return set()

def has_proper_sentences(text):
    """
    Check if text contains proper sentences (with punctuation).
    
    :param text: Text to check
    :return: Boolean indicating if text has proper sentences
    """
    # Check if text has sentence-ending punctuation
    sentence_endings = ['.', '!', '?']
    sentences = sent_tokenize(text)
    
    if len(sentences) < 2:
        # If there's only one sentence or less, check if it ends properly
        return any(text.strip().endswith(ending) for ending in sentence_endings)
    
    # If there are multiple sentences, it likely has proper structure
    return True

def clean_website_data(raw_text):
    """
    Cleans up raw website text data, removing common HTML artifacts and excess whitespace.
    """
    try:
        # Remove HTML tags (basic HTML tag removal)
        cleaned_text = re.sub('<[^<]+?>', '', raw_text)

        # Remove multiple spaces and newlines, and then trim
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        #Remove non-printing characters
        cleaned_text = ''.join(c for c in cleaned_text if c.isprintable())
        return cleaned_text

    except Exception as e:
        return json.dumps({"error": f"Error processing text: {str(e)}"})

def rank_sentences(text, stopwords, max_sentences=10):
    """
    Rank sentences in the text based on word frequency, returning top 'max_sentences' sentences.
    """
    word_frequencies = {}
    for word in word_tokenize(text.lower()):
        if word.isalpha() and word not in stopwords:  # Consider only alphabetic words
            word_frequencies[word] = word_frequencies.get(word, 0) + 1

    sentence_scores = {}
    sentences = sent_tokenize(text)
    for sent in sentences:
        for word in word_tokenize(sent.lower()):
            if word in word_frequencies and len(sent.split(' ')) < 30:
                sentence_scores[sent] = sentence_scores.get(sent, 0) + word_frequencies[word]

    sorted_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)
    summary_sentences = sorted_sentences[:max_sentences]
    
    # Add a full stop at the end of each sentence if it doesn't already end with one
    summary = ' '.join([s if s.endswith('.') else f'{s}.' for s in summary_sentences])

    return summary


# URL Shortener functions
def shorten_url(url, table_name=None, base_url=None, custom_code=None):
    """
    Convenience function to shorten a URL
    
    Args:
        url (str): The URL to shorten
        table_name (str): DynamoDB table name
        base_url (str): Base URL for shortened links
        custom_code (str): Optional custom short code
        
    Returns:
        dict: Result dictionary
    """
    shortener = URLShortener(table_name=table_name, base_url=base_url)
    return shortener.shorten_url(url, custom_code=custom_code)


# External Services functions
def get_coordinates(location_name):
    openweather_api_key = os.getenv('OPENWEATHER_KEY')
    base_url = 'http://api.openweathermap.org/geo/1.0/direct'
    params = {
        'q': location_name,
        'limit': 1,  # You may limit to 1 result for accuracy
        'appid': openweather_api_key
    }
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            # Extract latitude and longitude from the first result
            lat = data[0]['lat']
            lon = data[0]['lon']
            return lat, lon
    return None  # Return None if location not found or API request fails


def get_weather_data(location_name='Whitehorse'):
    openweather_api_key = os.getenv('OPENWEATHER_KEY')
    # Validate location_name  
    if not location_name.strip():
        return 'Location name is empty or contains only spaces. Please provide a valid location name.'

    coordinates = get_coordinates(location_name)  # This function needs to be defined
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

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return f'Failed to get weather data: {response.reason}'

    return response.json()


# Lambda function utilities
def get_embedding(text, model="text-embedding-ada-002"):
    text_cleaned = text.replace("\n", " ")
    embedding = client.embeddings.create(input=[text_cleaned], model=model).data[0].embedding
    return {"text": text_cleaned, "embedding": embedding}


def google_search(search_term, before=None, after=None, intext=None, allintext=None, and_condition=None, must_have=None):
    # Initialize API keys from environment variables
    custom_search_api_key = os.getenv('CUSTOM_SEARCH_API_KEY')
    custom_search_id = os.getenv('CUSTOM_SEARCH_ID')

    # Constructing the search term with advanced operators
    search_components = [search_term]

    # Implementing 'and' search operator
    if and_condition:
        search_components.append(search_term + " AND " + and_condition)

    # Implementing 'before' search operator (YYYY-MM-DD format)
    if before:
        search_components.append(f"before:{before}")

    # Implementing 'after' search operator (YYYY-MM-DD format)
    if after:
        search_components.append(f"after:{after}")

    # Implementing 'intext' search operator
    if intext:
        search_components.append(f"intext:{intext}")
    
    # Implementing 'allintext' search operator
    if allintext:
        search_components.append(f"allintext:{allintext}")
    
    # Implementing 'must_have' operator to require exact phrase match
    if must_have:
        search_components.append(f"\"{must_have}\"")  # Use of escaped quotes to handle Python string encapsulation

    # Join all components to form the final search query
    combined_search_term = ' '.join(search_components)
    url_encoded_search_term = quote_plus(combined_search_term)
    print(f'Search Term: {url_encoded_search_term}')

    # Build the search URL   
    search_url = f"https://www.googleapis.com/customsearch/v1?q={url_encoded_search_term}&cx={custom_search_id}&key={custom_search_api_key}"
    response = requests.get(search_url)
    results = response.json().get('items', [])
    print(json.dumps(results, default=decimal_default))

    web_links = []
    for result in results:
        web_links.append(result['link'])
    
    # Assuming get_web_pages is a coroutine to fetch web pages 
    web_content = asyncio.run(get_web_pages(web_links[:5]))
    print(json.dumps(web_content, default=decimal_default))  # Assuming decimal_default was a function for JSON serializing decimals   
    
    return web_content


def browse_internet(urls, full_text=False):
    try:
        # Suppress resource warnings in Lambda environment
        import warnings
        warnings.filterwarnings("ignore", category=ResourceWarning)
        
        web_pages = asyncio.run(get_web_pages(urls, full_text))
        #print(web_pages)
        return web_pages
    except asyncio.TimeoutError:
        logging.error(f"Timeout error in browse_internet for URLs: {urls}")
        return [{
            "type": "text",
            "text": {
                'error': 'Request timed out while fetching web pages',
                'urls': urls
            }
        }]
    except Exception as e:
        logging.error(f"Error in browse_internet: {e}")
        return [{
            "type": "text",
            "text": {
                'error': f'Failed to fetch web pages: {str(e)}',
                'urls': urls
            }
        }]


async def get_web_pages(urls, full_text=False, max_concurrent_requests=5):
    try:
        # Configure connector with explicit settings to prevent resource warnings
        connector = aiohttp.TCPConnector(
            limit=max_concurrent_requests,
            limit_per_host=2,
            force_close=True,  # Force close connections to prevent warnings
            enable_cleanup_closed=True  # Clean up closed connections immediately
        )
        
        async with aiohttp.ClientSession(connector=connector) as session:
            semaphore = asyncio.Semaphore(max_concurrent_requests)
            tasks = [process_page(session, url, semaphore, full_text) for url in urls]
            # Use return_exceptions=True to prevent gather from raising exceptions
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle any exceptions
            flattened_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logging.error(f"Error processing URL {urls[i]}: {result}")
                    flattened_results.append({
                        "type": "text",
                        "text": {
                            'url': urls[i],
                            'error': f'Failed to process page: {str(result)}'
                        }
                    })
                else:
                    flattened_results.extend(result)
            
            #print(json.dumps(flattened_results))
            return flattened_results
    except Exception as e:
        logging.error(f"Error in get_web_pages: {e}")
        # Return error responses for all URLs
        return [{
            "type": "text",
            "text": {
                'url': url,
                'error': f'Failed to fetch pages: {str(e)}'
            }
        } for url in urls]


async def fetch_page(session, url, timeout=30):
    headers = {
        'User-Agent': random.choice(USER_AGENTS)
    }
    
    # Create timeout object for both connection and read
    timeout_obj = aiohttp.ClientTimeout(total=timeout, connect=10, sock_read=timeout)
    
    try:
        async with session.get(url, headers=headers, proxy=proxy_url, timeout=timeout_obj) as response:
            #print(f"Search Result: {response}")
            content_type = response.headers.get('Content-Type', '')
            if 'text' in content_type:
                encoding = response.charset or 'utf-8'
                content = await response.text(encoding=encoding)
                # Explicitly release the connection
                response.release()
                return content
            elif 'application/pdf' in content_type or 'application/msword' in content_type or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
                content = await response.read()
                # Explicitly release the connection
                response.release()
                return content, content_type
            else:
                # Explicitly release the connection for non-text content
                response.release()
                return None, content_type
    except asyncio.TimeoutError:
        logging.error(f"Timeout error: {url} took too long to respond.")
        return f"Timeout error: {url} took too long to respond.", None
    except ClientConnectorSSLError as e:
        logging.error(f"SSL handshake error: Failed to connect to {url} - {e}")
        return f"SSL handshake error: Failed to connect to {url}", None
    except aiohttp.ClientError as e:
        logging.error(f"Client error fetching {url}: {e}")
        return f"Client error: {str(e)}", None
    except Exception as e:
        logging.error(f"Unexpected error fetching {url}: {e}")
        return f"Unexpected error: {str(e)}", None


def upload_document_to_s3(document_content, content_type, document_url):
    document_extension = mimetypes.guess_extension(content_type) or '.bin'
    s3_object_name = f"Document_{datetime.datetime.now(datetime.UTC).strftime('%Y%m%d%H%M%S')}{document_extension}"

    # Upload to S3
    s3_client = boto3.client('s3')
    s3_client.put_object(Body=document_content, Bucket=docs_bucket_name, Key=s3_object_name)

    # Construct the S3 URL
    s3_url = f"https://{docs_bucket_name}.s3.amazonaws.com/{s3_object_name}"
    return s3_url


async def process_page(session, url, semaphore, full_text=False):
    async with semaphore:
        try:
            result = await fetch_page(session, url)
        except ClientError as e:
            logging.error(f"Client error occurred while fetching the page: {e}")
            print(f"Client error occurred while fetching {url}: {e}")
            return [{
                "type": "text",
                "text": {
                    'url': url,
                    'error': 'Failed to fetch page due to client error'
                }
            }]
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")
            print(f"Unexpected error occurred while fetching {url}: {e}")
            return [{
                "type": "text",
                "text": {
                    'url': url,
                    'error': 'An unexpected error occurred while fetching the page'
                }
            }]
        
        response_list = []

        #print(f'Raw Result: {result}')
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
                        print(f"Failed to upload document to S3 for {url}: {e}")
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

                # Load stopwords if not already loaded
                global stopwords
                if not stopwords:
                    stopwords = load_stopwords('english')

                if full_text:
                    if has_proper_sentences(cleaned_text):
                        summary_or_full_text = rank_sentences(cleaned_text, stopwords, max_sentences=150)
                    else:
                        summary_or_full_text = cleaned_text
                else:
                    try:
                        if has_proper_sentences(cleaned_text):
                            summary_or_full_text = rank_sentences(cleaned_text, stopwords, max_sentences=50)
                        else:
                            summary_or_full_text = cleaned_text
                    except Exception as e:
                        logging.error(f"Failed to rank sentences: {e}")
                        print(f"Failed to rank sentences for {url}: {e}")
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
                            #logging.warning(f"Skipping data URI image: {img_url[:30]}...")  # Log a warning and skip data URIs
                            continue
                        if not img_url.startswith(('http://', 'https://')):
                            img_url = urljoin(url, img_url)
                        
                        try:
                            # Use a short timeout for HEAD requests
                            head_timeout = aiohttp.ClientTimeout(total=5, connect=2)
                            async with session.head(img_url, timeout=head_timeout) as img_response:
                                if img_response.status == 200 and int(img_response.headers.get('Content-Length', 0)) > 10240:
                                    response_list.append({
                                        "type": "image_url",
                                        "image_url": {
                                            'url': img_url
                                        }
                                    })
                                # Explicitly release the connection
                                img_response.release()
                        except asyncio.TimeoutError:
                            # Silently skip images that timeout - not critical
                            pass
                        except ClientError as e:
                            logging.error(f"Failed to fetch image: {img_url} - ClientError: {e}")
                            print(f"Failed to fetch image {img_url}: ClientError - {e}")
                        except Exception as e:
                            logging.error(f"Failed to fetch image: {img_url} - Unexpected error: {e}")
                            print(f"Failed to fetch image {img_url}: Unexpected error - {e}")
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
            print(f"Error processing page {url}: {e}")
            response_list.append({
                "type": "text",
                "text": {
                    'url': url,
                    'error': 'An error occurred while processing the page'
                }
            })

        return response_list


def send_as_pdf(text, chat_id, title, ts=None):
    """
    Converts formatted text to PDF and uploads it to a Slack channel.
    Returns a clear status string after execution.
    """
    pdf_path = f"/tmp/{title}.pdf"
    try:
        # Use a Unicode-supporting font
        pdf = MyFPDF(title)
        pdf.add_page()
        # Register and use a Unicode font (e.g., DejaVu)
        pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
        pdf.set_font('DejaVu', '', 11)

        # Convert Markdown to HTML
        text = text.replace("\n\n", "\n")
        html_content = markdown2.markdown(text)
        html_content = replace_problematic_chars(html_content)
        pdf.write_html(html_content)

        pdf.output(pdf_path, 'F')

        # Upload to S3
        bucket_name = docs_bucket_name
        folder_name = 'uploads'
        file_key = f"{folder_name}/{title}.pdf"
        s3_client = boto3.client('s3')
        s3_client.upload_file(pdf_path, bucket_name, file_key)

        # Upload to Slack
        from slack_integration import send_file_to_slack
        send_file_to_slack(pdf_path, chat_id, title, ts)
        status = "Success: PDF sent to Slack and uploaded to S3."

    except Exception as e:
        status = f"Failure: {e}"

    finally:
        # Clean up
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    return status


def list_files(folder_prefix='uploads'):
    """
    Lists the files in a specified folder in the 'docs_bucket_name' S3 bucket.

    Parameters:
    - folder_prefix: The prefix of the folder whose files you want to list (optional). This should end with a slash ('/') if provided.   

    Returns:
    - A dictionary where each key is the file name and the value is the object URL.
    """
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=docs_bucket_name, Prefix=folder_prefix)

    files = {}
    if 'Contents' in response:
        for obj in response['Contents']:
            if not obj['Key'].endswith('/'):  # Exclude any subfolders
                file_url = f"https://{docs_bucket_name}.s3.amazonaws.com/{obj['Key']}"
                file_name = obj['Key'].split('/')[-1]  # Extract the file name from the key
                files[file_name] = file_url

    return files


def solve_maths(code: str, **params) -> dict:
    """
    Execute the given code and return the result.

    Parameters:
    - code (str): The Python code to execute.
    - **params: Any parameters that the code might need.

    Returns:
    - dict: A dictionary containing the result or an error message.
    """
    exec_env = {}
    exec_env.update(params)
    
    try:
        exec(code, {}, exec_env)
        
        # Filter out non-serializable objects
        serializable_result = {key: value for key, value in exec_env.items() if is_serializable(value)}
        
        return {"status": "success", "result": serializable_result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Storage functions
def get_message_by_sort_id(role, chat_id, sort_id):
    try:
        # Determine the appropriate collection based on the role
        if role == "user":
            collection = weaviate_client.collections.get('UserMessages')
        elif role == "assistant":
            collection = weaviate_client.collections.get('AssistantMessages')
        else:
            return None  # Handle unexpected roles

        timestamp = int(sort_id)
        timestamp_iso = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).isoformat()
        
        # Create filters to match chat_id and sort_id
        filters = (
            Filter.by_property("chat_id").equal(chat_id)
            & Filter.by_property("timestamp").equal(timestamp_iso)
        )

        # Fetch the single matching object
        response = collection.query.fetch_objects(
            filters=filters,
            limit=1  # Expecting only one item
        )

        message = response.objects[0].properties.get('message') if response.objects else None
        print(f"Single Message: {message}")
        return message
    except Exception as e:
        print(f"Error retrieving message by sort ID: {e}")
        return None


def get_messages_in_range(chat_id, start_sort_id, end_sort_id):
    try:
        # Retrieve user and assistant messages
        user_collection = weaviate_client.collections.get("UserMessages")
        assistant_collection = weaviate_client.collections.get("AssistantMessages")

        # Define filters for both collections using the correct timestamp conversion
        start_date = datetime.datetime.fromtimestamp(start_sort_id, datetime.timezone.utc).isoformat()
        end_date = datetime.datetime.fromtimestamp(end_sort_id, datetime.timezone.utc).isoformat()
        print(f"Start Date: {start_date}")
        print(f"End Date: {end_date}")

        # Define filters for both collections
        filters = Filter.by_property("chat_id").equal(chat_id) & Filter.by_property("timestamp").greater_or_equal(start_date) & Filter.by_property("timestamp").less_or_equal(end_date)

        # Fetch user messages
        user_messages_response = user_collection.query.fetch_objects(
            filters=filters
        )
        user_messages = transform_objects(user_messages_response.objects if user_messages_response.objects else [], "UserMessages")
        print(f"User Messages: {user_messages}")

        # Fetch assistant messages
        assistant_messages_response = assistant_collection.query.fetch_objects(
            filters=filters
        )
        assistant_messages = transform_objects(assistant_messages_response.objects if assistant_messages_response.objects else [], "AssistantMessages")
        print(f"Assistant Messages: {assistant_messages}")

        # Combine and sort messages
        all_messages = user_messages + assistant_messages
        all_messages.sort(key=lambda x: x["sort_key"])

        return all_messages
    except Exception as e:
        print(f"Error retrieving messages in range: {e}")
        return []


def get_users(user_id=None):
    try:
        if user_id:
            # Retrieve a single user
            response = names_table.get_item(Key={'user_id': user_id})
            item = response.get('Item', None)
            if item:
                return item
            else:
                from slack_integration import update_slack_users
                update_slack_users()
                response = names_table.get_item(Key={'user_id': user_id})
                item = response.get('Item', None)
                if item:
                    return item
                else:
                    print(user_id, " still not found after update.")
                    return None
        else:
            # Retrieve all users
            response = names_table.scan()
            items = response.get('Items', [])
            return items
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_channels(id=None):
    try:
        from slack_integration import update_slack_conversations
        update_slack_conversations()
        # Perform a scan operation on the table to retrieve all channels  
        response = channels_table.scan()
        channels = response.get('Items', [])

        # Check if there are more channels to fetch
        while 'LastEvaluatedKey' in response:
            response = channels_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            channels.extend(response.get('Items', []))

        return channels
    except Exception as e:
        print(f"Error fetching channels: {e}")
        return []


def manage_mute_status(chat_id, status=None):
    table = channels_table
    
    if status is not None:
        # Initialize status_bool based on the type and value of status
        if isinstance(status, bool):
            status_bool = status
        elif isinstance(status, str):
            status = status.strip()  # Remove any leading/trailing whitespace
            if status.lower() in ['true', 'false']:
                status_bool = status.lower() == 'true'
            else:
                raise ValueError("String status must be 'true' or 'false' (case insensitive).")
        else:
            raise TypeError("Status must be provided as either a boolean or a string.")

        try:
            response = table.update_item(
                Key={
                    'id': chat_id
                },
                UpdateExpression='SET maria_status = :val',
                ExpressionAttributeValues={
                    ':val': status_bool
                },
                ReturnValues='UPDATED_NEW'
            )
            current_status = "true" if status_bool else "false"
            return [status_bool, f"Current mute status: {current_status}"]
        except ClientError as e:
            print(f"An error occurred: {e}")
            raise
    else:
        try:
            response = table.get_item(
                Key={
                    'id': chat_id
                }
            )
            item = response.get('Item', {})
            maria_status = item.get('maria_status', None)

            if maria_status is None:
                status_bool = False  # Assuming False as default if status doesn't exist
                current_status = "false"
                print("The 'maria_status' attribute does not exist for this record.")
            else:
                status_bool = maria_status  # Assuming maria_status is stored as a boolean
                current_status = "true" if maria_status else "false"
            
            return [status_bool, f"Current mute status: {current_status}"]
        except ClientError as e:
            print(f"An error occurred: {e}")
            raise


# Odoo functions
def authenticate(odoo_url, db, login, password):
    """Authenticate with Odoo and return session info"""
    auth_url = f"{odoo_url}/web/session/authenticate"
    headers = {'Content-Type': 'application/json'}
    payload = {
        'jsonrpc': '2.0',
        'method': 'call',
        'params': {
            'db': db,
            'login': login,
            'password': password
        },
        'id': 1
    }
    
    try:
        response = requests.post(auth_url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if 'error' in result:
            return {'error': result['error']}
        
        session_id = response.cookies.get('session_id')
        if not session_id:
            return {'error': 'No session ID received'}
            
        return {
            'session_id': session_id,
            'uid': result.get('result', {}).get('uid'),
            'username': result.get('result', {}).get('username')
        }
    except Exception as e:
        return {'error': str(e)}


def odoo_get_mapped_models(include_fields=True, model_name=None):
    """
    Fetches available mapped models.
    
    Args:
    - include_fields (bool): Whether to include field mappings.
    - model_name (str): Optional filter for model names.
    
    Returns:
    - dict: Response containing mapped models.
    """
    # Authenticate first
    auth_result = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
    if 'error' in auth_result:
        return auth_result
    
    session_id = auth_result['session_id']
    endpoint = f"{base_url}/api/mapped_models"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    params = {}
    payload = {}
    
    if include_fields:
        params['include_fields'] = include_fields
    if model_name:
        params['model_name'] = model_name
    payload['params'] = params
    try: 
        print(json.dumps(payload))
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}


def odoo_fetch_records(external_model, filters=None):
    """
    Retrieves records from an external model.
    
    Args:
    - base_url (str): Base URL for the API middleware.
    - odoo_url (str): The base URL of the Odoo instance.
    - db (str): The database name.
    - login (str): The user's login name.
    - password (str): The user's password.
    - external_model (str): External model name.
    - filters (list): Optional Odoo domain filters.
    
    Returns:
    - dict: Response containing records.
    """
    # Authenticate first
    auth_result = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
    if 'error' in auth_result:
        return auth_result
    
    session_id = auth_result['session_id']
    endpoint = f"{base_url}/api/{external_model}"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    payload = {}
    
    if filters:
        payload['filters'] = filters
        
    try:
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}


def odoo_create_record(external_model, record_data):
    """
    Creates a new record.
    Args:
        external_model (str): External model name.
        record_data (dict): Data for the record to be created.
    Returns:
        dict: Response containing the created record or error.
    """
    # Check for missing parameters
    if not external_model:
        return {'error': "Missing required parameter: 'external_model'."}
    if not record_data:
        return {'error': "Missing required parameter: 'record_data'."}
    if not isinstance(record_data, dict):
        return {'error': "'record_data' must be a dictionary."}
    
    # Authenticate first
    auth_result = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
    if 'error' in auth_result:
        return auth_result
    session_id = auth_result['session_id']
    endpoint = f"{base_url}/api/{external_model}/create"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    payload = {'params': record_data}
    try:
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}


def odoo_update_record(external_model, record_id, **kwargs):
    """
    Updates an existing record.
    Args:
    - external_model (str): External model name.
    - record_id (int): ID of the record to update.
    - **kwargs: Variable keyword arguments that will be combined into record_data.
    
    Returns:
    - dict: Response containing the updated record.
    """
    # Authenticate first
    auth_result = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
    if 'error' in auth_result:
        return auth_result
    
    session_id = auth_result['session_id']
    endpoint = f"{base_url}/api/{external_model}/update/{record_id}"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    
    # Using kwargs directly as the record_data
    record_data = kwargs
    
    try:
        response = requests.put(endpoint, headers=headers, json=record_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}


def odoo_delete_record(external_model, record_id):
    """
    Deletes a record.
    
    Args:
    - base_url (str): Base URL for the API middleware.
    - odoo_url (str): The base URL of the Odoo instance.
    - db (str): The database name.
    - login (str): The user's login name.
    - password (str): The user's password.
    - external_model (str): External model name.
    - record_id (int): ID of the record to delete.
    
    Returns:
    - dict: Response indicating success or failure.
    """
    # Authenticate first
    auth_result = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
    if 'error' in auth_result:
        return auth_result
    
    session_id = auth_result['session_id']
    endpoint = f"{base_url}/api/{external_model}/delete/{record_id}"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    
    try:
        response = requests.delete(endpoint, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}


def odoo_print_record(model_name, record_id):
    """
    Prints the specified record (subject to the record being printable).
    
    Args:
    - model_name (str): The technical name of the model.
    - record_id (int): The ID of the document to print.
    
    Returns:
    - dict: A dictionary containing the result of the print request or an error message.
    """
    auth_response = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
    if 'session_id' not in auth_response:
        return auth_response
    
    session_id = auth_response['session_id']
    endpoint = f"{odoo_url}/api/generate_pdf"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    payload = {
        "params": {
            "external_model": model_name,
            "record_id": record_id
        }
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(endpoint, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req) as resp:
            response_data = resp.read().decode()
            print(f"Response content: {response_data}")  # Log response content for debugging
            response_data = json.loads(response_data)
            full_url = response_data["result"]["download_url"]
            print(f'Full Url: {full_url}')
            result = shorten_url(full_url)
            print(f'Shortened Url: {result}')
            result.pop('originalUrl', None)
            return result
    except urllib.error.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except json.JSONDecodeError as json_err:
        return {'error': f'JSON decode error occurred: {json_err} - Response content: {response_data}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}


def odoo_post_record(external_model, record_id):
    """
    Posts a record using the specified external model and record ID.
    
    Args:
    - external_model (str): External model name.
    - record_id (int): ID of the record to post.
    
    Returns:
    - dict: Response containing the result of the post operation or error.
    """
    # Authenticate first
    auth_result = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
    if 'error' in auth_result:
        return auth_result
    
    session_id = auth_result['session_id']
    # Properly encode the external_model for URL
    encoded_model = urllib.parse.quote(external_model, safe='')
    endpoint = f"{base_url}/api/{encoded_model}/post/{record_id}"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    
    try:
        # Include an empty JSON payload for the PUT request
        response = requests.put(endpoint, headers=headers, json={})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}


# Conversation functions
def ask_openai_o1(prompt):
    print(f'OpenAI o1 Prompt: {prompt}')
    message = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    try:
        # Prepare the API call
        response = client.chat.completions.create(
            model="o3-mini-2025-01-31",
            messages=message
        )
        print(f'OpenAI o1: {response}')
        
        # Extract the actual message content using dot notation
        response_message_content = response.choices[0].message.content

        # Return the serialized content
        return json.dumps(response_message_content, default=decimal_default)
    except Exception as e:
        print(f"An error occurred during the OpenAI o1 API call: {e}")
        return None


# Amazon functions
def search_and_format_products(
    query: str,
    country: str = "US",
    max_products: int = 5,
    **kwargs
) -> str:
    """
    Search for products on Amazon and return formatted results.
    
    Parameters:
    ----------
    query : str
        The search term to query Amazon with
    country : str, optional
        The Amazon marketplace country code (default: "US")
    max_products : int, optional
        Maximum number of products to show in results (default: 5)
    **kwargs :
        Additional parameters to pass to the search_amazon_products function
        
    Returns:
    -------
    str
        A formatted string containing the product information
    """
    response = search_amazon_products(query=query, country=country, **kwargs)
    return format_product_results(response, max_products)


def search_amazon_products(
    query: str,
    country: str = "CA",
    page: int = 1,
    sort_by: str = "RELEVANCE",
    product_condition: str = "NEW",
    is_prime: bool = False,
    deals_and_discounts: str = "NONE"
) -> Dict[str, Any]:
    """
    Search for products on Amazon using the Real-Time Amazon Data API from RapidAPI.
    
    Parameters:
    ----------
    query : str
        The search term to query Amazon with
    country : str, optional
        The Amazon marketplace country code (default: "US")
    page : int, optional
        The page number of results (default: 1)
    sort_by : str, optional
        How to sort the results (default: "RELEVANCE")
        Options: "RELEVANCE", "PRICE_LOW_TO_HIGH", "PRICE_HIGH_TO_LOW", "RATING", "NEWEST"
    product_condition : str, optional
        Product condition filter (default: "NEW")
        Options: "NEW", "USED", "REFURBISHED"
    is_prime : bool, optional
        Filter for Amazon Prime eligible products (default: False)
    deals_and_discounts : str, optional
        Filter for deals and discounts (default: "NONE")
        Options: "NONE", "TODAY_DEALS", "ON_SALE"
        
    Returns:
    -------
    Dict[str, Any]
        The full API response as a dictionary
    """
    url = "https://real-time-amazon-data.p.rapidapi.com/search"
    
    # Convert boolean to string for the API
    is_prime_str = str(is_prime).lower()
    
    querystring = {
        "query": query,
        "country": country,
        "page": str(page),
        "sort_by": sort_by,
        "product_condition": product_condition,
        "is_prime": is_prime_str,
        "deals_and_discounts": deals_and_discounts
    }
    
    headers = {
        "X-RapidAPI-Key": "4c37223acemsh65b1a8b456b72c1p15a99ajsnd4a09ab346a4",
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "ERROR", "message": str(e)}


def format_product_results(response_data: Dict[str, Any], max_products: int = 5) -> str:
    """
    Format the API response data into a readable string format.
    
    Parameters:
    ----------
    response_data : Dict[str, Any]
        The API response data
    max_products : int, optional
        Maximum number of products to include in the formatted output (default: 5)
        
    Returns:
    -------
    str
        A formatted string containing the product information
    """
    if response_data.get("status") != "OK":
        return f"Error: {response_data.get('message', 'Unknown error')}"
    
    data = response_data.get("data", {})
    total_products = data.get("total_products", 0)
    products = data.get("products", [])
    
    if not products:
        return "No products found."
    
    result = f"Found {total_products} products. Showing top {min(max_products, len(products))}:\n\n"
    
    for i, product in enumerate(products[:max_products], 1):
        title = product.get("product_title", "No title")
        price = product.get("product_price", "Price not available")
        rating = product.get("product_star_rating", "No rating")
        num_ratings = product.get("product_num_ratings", 0)
        url = product.get("product_url", "URL not available")
        
        result += f"{i}. {title}\n"
        result += f"   Price: {price}\n"
        result += f"   URL: {url}\n"
        
        if rating and num_ratings:
            result += f"   Rating: {rating}/5 ({num_ratings} reviews)\n"
        
        # Add best seller or Amazon's choice badge if applicable
        if product.get("is_best_seller"):
            result += f"   🏆 Best Seller\n"
        if product.get("is_amazon_choice"):
            result += f"   ✅ Amazon's Choice\n"
        
        # Add delivery information if available
        delivery = product.get("delivery")
        if delivery:
            result += f"   Delivery: {delivery}\n"
        
        result += "\n"
    
    return result


# Slack integration functions
def send_file_to_slack(file_path, chat_id, title, ts=None):
    """
    Uploads a file to a specified Slack channel using the external upload API.
    If the file_path is a URL, downloads the file first.
    
    Parameters:
    - file_path: The path to the file or a URL
    - chat_id: The ID of the Slack channel where the file will be uploaded
    - title: The title of the file
    - ts: The thread timestamp (optional)
    
    Returns:
    - dict: The JSON response from the files.completeUploadExternal API
    """
    # Check if file_path is a URL
    parsed_url = urlparse(file_path)
    is_url = parsed_url.scheme in ('http', 'https')
    
    if is_url:
        # Download the file into a temporary file
        response = requests.get(file_path)
        response.raise_for_status()  # Ensure the download succeeded
        suffix = os.path.splitext(parsed_url.path)[1]  # Extract the file extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(response.content)
            file_to_upload = tmp_file.name
    else:
        file_to_upload = file_path

    try:
        # Get file details
        file_size = os.path.getsize(file_to_upload)
        file_name = os.path.basename(file_to_upload)
        
        # Step 1: Get upload URL
        headers = {
            "Authorization": f"Bearer {slack_bot_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        url_params = {
            "filename": file_name,
            "length": file_size
        }
        
        response = requests.get(
            "https://slack.com/api/files.getUploadURLExternal",
            headers=headers,
            params=url_params
        )
        
        if not response.ok or not response.json().get("ok"):
            error = response.json().get("error", "Unknown error")
            print(f"Error getting upload URL: {error}")
            return response.json()
        
        upload_url = response.json()["upload_url"]
        file_id = response.json()["file_id"]
        
        # Step 2: Upload file to the provided URL
        with open(file_to_upload, "rb") as file:
            # Determine content type based on file extension
            import mimetypes
            file_extension = os.path.splitext(file_to_upload)[1].lower()
            content_type = mimetypes.guess_type(file_to_upload)[0] or "application/octet-stream"
            
            files = {
                "file": (file_name, file, content_type)
            }
            upload_response = requests.post(upload_url, files=files)
        
        if not upload_response.ok:
            print(f"Error uploading file: {upload_response.status_code}")
            return {"ok": False, "error": "upload_failed"}
        
        # Step 3: Complete the upload
        complete_data = {
            "files": [{
                "id": file_id,
                "title": title
            }],
            "channel_id": chat_id
        }
        
        if ts:
            complete_data["thread_ts"] = ts
        
        complete_response = requests.post(
            "https://slack.com/api/files.completeUploadExternal",
            headers={
                "Authorization": f"Bearer {slack_bot_token}",
                "Content-Type": "application/json"
            },
            json=complete_data
        )
        
        if complete_response.ok and complete_response.json().get("ok"):
            print(f"File uploaded successfully: {file_id}")
        else:
            error = complete_response.json().get("error", "Unknown error")
            print(f"Error completing upload: {error}")
        
        return complete_response.json()
        
    finally:
        if is_url:
            # Remove the temporary file
            os.unlink(file_to_upload)


def update_slack_users():
    url = 'https://slack.com/api/users.list'
    headers = {
        'Authorization': f'Bearer {slack_bot_token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        users_list = response.json().get('members', [])
        for user in users_list:
            if not user.get('deleted', True) and not user.get('is_bot', True) and not user.get('is_app_user', True):
                user_id = user.get('id')
                try:
                    response = names_table.get_item(Key={'user_id': user_id})
                    item = response.get('Item', None)
                    if item:
                        print(f"User {user_id} already exists in the database.")
                        # Check if all keys are available
                        missing_keys = [key for key in ['real_name', 'display_name', 'email'] if key not in item]
                        if missing_keys:
                            print(f"Updating user {user_id} with missing keys: {missing_keys}")
                            for key in missing_keys:
                                item[key] = user.get('profile', {}).get(key, '')
                            names_table.put_item(Item=item)
                            print(f"User {user_id} updated successfully.")
                    else:
                        print(f"Adding user {user_id} to the database.")
                        user_data = {
                            'user_id': user_id,
                            'real_name': user.get('profile', {}).get('real_name', ''),
                            'display_name': user.get('profile', {}).get('display_name', ''),
                            'email': user.get('profile', {}).get('email', '')
                        }
                        names_table.put_item(Item=user_data)
                        print(f"User {user_id} added successfully.")
                except Exception as e:
                    print(f"Error processing user {user_id}: {e}")
    else:
        print(f"Failed to retrieve users list: HTTP {response.status_code}")


def update_slack_conversations():
    url = 'https://slack.com/api/conversations.list'
    headers = {
        'Authorization': f'Bearer {slack_bot_token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    params = {
        'types': 'public_channel,private_channel'
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        conversations_list = response.json().get('channels', [])
        for channel in conversations_list:
            channel_id = channel.get('id')
            try:
                # Retrieve the existing channel details from DynamoDB
                existing_channel = channels_table.get_item(Key={'id': channel_id})
                
                if 'Item' in existing_channel:
                    print(f"Channel {channel_id} already exists in the database.")
                    # Existing channel: update if necessary
                    channels_table.update_item(
                        Key={'id': channel_id},
                        UpdateExpression="set #info.#name=:n, #info.#is_private=:p, #info.#num_members=:m",
                        ExpressionAttributeValues={
                            ':n': channel.get('name'),
                            ':p': channel.get('is_private'),
                            ':m': channel.get('num_members')
                        },
                        ExpressionAttributeNames={
                            "#info": "info",
                            "#name": "name",  # Using an expression attribute name as a placeholder
                            "#is_private": "is_private",
                            "#num_members": "num_members"
                        }
                    )
                else:
                    # New channel: add to the database
                    channels_table.put_item(Item=channel)
                    print(f"Channel {channel_id} added to the database.")

            except Exception as e:
                print(f"Error updating channel {channel_id}: {e}")
    else:
        print(f"Failed to retrieve conversations list: HTTP {response.status_code}")


# Note: All functions have been included in this module for independent use.
# Some functions may require additional configuration or environment variables to work properly.