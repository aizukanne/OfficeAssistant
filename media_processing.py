import aiohttp
import asyncio
import base64
import boto3
import csv
import datetime
import json
import logging
import mimetypes
import openpyxl
import os
import PyPDF2
import random
import re
import requests
import tempfile
import warnings
import wave
from typing import Dict, Any

from aiohttp import ClientError, ClientConnectorSSLError
from bs4 import BeautifulSoup
from config import client, slack_bot_token, image_bucket_name, docs_bucket_name, USER_AGENTS, gemini_api_key
from concurrent.futures import ThreadPoolExecutor, as_completed
from docx import Document
from io import BytesIO, StringIO
from urllib.parse import urlparse, urljoin, unquote

from nlp_utils import (
    load_stopwords, rank_sentences, summarize_record, summarize_messages,
    clean_website_data
)


# Import additional dependencies for file processing
try:
    from nlp_utils import rank_sentences, load_stopwords
except ImportError:
    def rank_sentences(text, stopwords, max_sentences=25):
        return text[:1000]  # Fallback
    def load_stopwords(language):
        return []

stopwords = load_stopwords('english')


def text_to_speech(text, file_suffix=".mp3"):
    """
    Converts text to speech and saves the audio to a temporary file.

    Parameters:
    - text: The text to be converted to speech.
    - file_suffix: The suffix for the temporary file.

    Returns:  
    - The path to the saved speech file.    
    """
    with tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False) as tmp_file:
        with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="shimmer",
            input=text
        ) as response:
            response.stream_to_file(tmp_file.name)
        tmp_file_path = tmp_file.name

    return tmp_file_path


def upload_image_to_s3(image_url, bucket_name):
    # Download the image   
    headers = {
        'Authorization': f'Bearer {slack_bot_token}',
        'Content-Type': 'image/x-www-form-urlencoded'
    }
    response = requests.get(image_url, headers=headers)   

    if response.status_code != 200:
        raise Exception('Failed to download image')
        
    # Get the image content  
    image_content = BytesIO(response.content)

    file_extension = os.path.splitext(image_url)[1]
    s3_object_name = f"Maria_{datetime.datetime.now(datetime.UTC).strftime('%Y%m%d%H%M%S')}{file_extension}"

    # Upload to S3
    s3_client = boto3.client('s3')
    s3_client.upload_fileobj(image_content, bucket_name, s3_object_name)

    # Construct the S3 URL    
    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_object_name}"
    return s3_url


def transcribe_speech_from_memory(audio_stream, audio_format='.m4a'):
    """
    Transcribe audio from memory stream with support for different formats
    
    Args:
        audio_stream: BytesIO stream containing audio data
        audio_format: File extension for the audio format (e.g., '.m4a', '.ogg', '.mp3')
    """
    # Reset the stream's position to the beginning
    audio_stream.seek(0)

    # Create a temporary file to store the audio content
    with tempfile.NamedTemporaryFile(suffix=audio_format, delete=False) as tmp_file:
        tmp_file.write(audio_stream.read())
        tmp_file_path = tmp_file.name

    # Open the temporary file for reading
    with open(tmp_file_path, 'rb') as audio_file:
        # Create a transcription using OpenAI's Whisper model
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

    # Remove the temporary file  
    os.remove(tmp_file_path)
    return response.text


def download_audio_to_memory(url):
    headers = {
        'Authorization': f'Bearer {slack_bot_token}',
        'Content-Type': 'audio/x-www-form-urlencoded'
    }    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception('Failed to download audio')
        
    audio_content = BytesIO(response.content)
    
    response.raise_for_status()
    return audio_content


def download_telegram_audio_to_memory(url):
    """
    Download audio from Telegram file URL (no authorization needed)
    """
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f'Failed to download Telegram audio: {response.status_code}')
        
    audio_content = BytesIO(response.content)
    return audio_content


def process_url(url, platform='slack'):
    try:
        if platform == 'telegram':
            audio_stream = download_telegram_audio_to_memory(url)
            # Telegram voice messages are typically in OGG format
            transcription = transcribe_speech_from_memory(audio_stream, audio_format='.ogg')
        else:
            audio_stream = download_audio_to_memory(url)
            # Slack audio files are typically in M4A format
            transcription = transcribe_speech_from_memory(audio_stream, audio_format='.m4a')
        print(f"Success: Transcription completed for URL: {url}")
        return transcription
    except Exception as e:
        print(f"Failure: Could not process URL: {url}. Error: {str(e)}")
        return None


def process_telegram_url(url):
    """Process Telegram audio URL specifically"""
    return process_url(url, platform='telegram')


def transcribe_multiple_urls(urls, platform='slack'):
    results = []
    print(f'Transcribing audio from {platform}: {urls}')
    with ThreadPoolExecutor() as executor:
        if platform == 'telegram':
            # Use Telegram-specific processing
            future_to_url = {executor.submit(process_telegram_url, url): url for url in urls}
        else:
            # Use Slack processing (original behavior)
            future_to_url = {executor.submit(process_url, url): url for url in urls}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results.append(future.result())
            except Exception as exc:
                print(f'{url} generated an exception: {exc}')
    print(results)
    return results


def download_and_read_file(url, content_type, platform='slack'):
    """Download and read file content with platform-specific handling"""
    if platform == 'telegram':
        # Telegram files don't need authorization headers
        headers = {}
    else:
        # Slack files need authorization
        headers = {
            'Authorization': f'Bearer {slack_bot_token}',
            'Content-Type': 'image/x-www-form-urlencoded'
        }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Extract the original file name and extension from the URL    
        parsed_url = urlparse(url)
        original_file_name = os.path.basename(unquote(parsed_url.path))
        _, file_extension = os.path.splitext(original_file_name)

        # Define the S3 bucket and folder where the file will be saved 
        bucket_name = docs_bucket_name
        folder_name = 'uploads'

        # Use the original file extension for the temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(response.content)
            tmp_file.seek(0)
            
            # Upload the file to S3 with the original file name    
            file_key = f"{folder_name}/{original_file_name}"
            s3_client = boto3.client('s3')
            s3_client.upload_file(tmp_file.name, bucket_name, file_key)

            if 'text/csv' in content_type:
                f = StringIO(response.text)
                reader = csv.reader(f)
                return '\n'.join([','.join(row) for row in reader])
            elif 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type:
                workbook = openpyxl.load_workbook(tmp_file.name)
                sheet = workbook.active
                return '\n'.join([','.join([str(cell.value) for cell in row]) for row in sheet.rows])
            elif 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
                doc = Document(tmp_file.name)
                content = '\n'.join([p.text for p in doc.paragraphs])
                summary = rank_sentences(content, stopwords, max_sentences=50)
                return summary
            elif 'application/pdf' in content_type:
                pdf_reader = PyPDF2.PdfReader(tmp_file.name)
                text = ' '.join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
                # Remove excessive whitespace and newlines
                cleaned_text = ' '.join(text.split())
                print(f'PDF Contents: {cleaned_text}')
                if has_proper_sentences(cleaned_text):
                    summary = rank_sentences(cleaned_text, stopwords, max_sentences=50)
                    return summary
                else:                
                    return cleaned_text
            elif 'text/plain' in content_type:
                with open(tmp_file.name, 'r') as f:
                    content = f.read()
                return content
            else:
                return 'Unsupported file type'
    except Exception as e:
        return f'Error processing file: {e}'


def has_proper_sentences(text):
    """Simple check for proper sentences"""
    from nltk.tokenize import sent_tokenize
    
    sentences = sent_tokenize(text)
    
    # Check for sentences that end with proper punctuation and have reasonable length
    proper_sentences = [s for s in sentences if s.strip().endswith(('.', '!', '?')) and len(s.split()) > 5]
    
    return len(proper_sentences) >= 2

def convert_to_wav_in_memory(m4a_data):
    """
    Converts in-memory M4A/MP4 audio data to WAV format.
    Assumes the input is raw PCM audio data.

    Args:
        m4a_data (bytes): Audio data from M4A/MP4.

    Returns:
        bytes: Converted WAV data in memory.

    Raises:
        ValueError: If the input audio data is invalid.
        RuntimeError: If WAV conversion fails.
    """
    # Create an in-memory buffer for the output WAV file
    wav_buffer = BytesIO()

    try:
        # Open the buffer as a WAV file for writing
        with wave.open(wav_buffer, "wb") as wav_file:
            # Set the required WAV parameters
            wav_file.setnchannels(2)  # Stereo
            wav_file.setsampwidth(2)  # 16-bit samples (2 bytes per sample)
            wav_file.setframerate(44100)  # 44.1 kHz sample rate

            # Write the raw PCM audio data to the WAV file
            wav_file.writeframes(m4a_data)

        # Return WAV data as bytes
        wav_buffer.seek(0)  # Rewind buffer to the beginning
        return wav_buffer.read()

    except wave.Error as e:
        raise ValueError("Invalid WAV data or parameters.") from e

    except Exception as e:
        raise RuntimeError("An error occurred during WAV conversion.") from e

    finally:
        wav_buffer.close()


class EnhancedWebScraper:
    """Enhanced web scraper with content filtering to prevent problematic files"""
    
    def __init__(self):
        # Content type filtering
        self.ALLOWED_CONTENT_TYPES = {
            'text/html',
            'text/plain',
            'application/xhtml+xml',
            'text/xml',
            'application/xml'
        }
        
        # File extensions to avoid
        self.BLOCKED_EXTENSIONS = {
            '.counts', '.dat', '.bin', '.exe', '.zip', '.tar', '.gz',
            '.csv', '.tsv', '.json', '.log', '.db', '.sql'
        }
        
        # URL patterns to avoid (data files, APIs, etc.)
        self.BLOCKED_URL_PATTERNS = [
            r'\.counts$',
            r'/api/',
            r'/data/',
            r'\.json$',
            r'\.csv$',
            r'\.tsv$',
            r'\.xml$',
            r'\.rss$',
            r'/feed',
            r'googlelist\.counts'  # Specifically block the problematic file
        ]
    
    def should_process_url(self, url):
        """Check if a URL should be processed based on various filters."""
        try:
            parsed_url = urlparse(url)
            
            # Check file extension
            path = parsed_url.path.lower()
            for ext in self.BLOCKED_EXTENSIONS:
                if path.endswith(ext):
                    logging.info(f"Blocking URL due to extension: {url}")
                    return False
            
            # Check URL patterns
            for pattern in self.BLOCKED_URL_PATTERNS:
                if re.search(pattern, url, re.IGNORECASE):
                    logging.info(f"Blocking URL due to pattern match: {url}")
                    return False
            
            return True
        except Exception as e:
            logging.error(f"Error checking URL {url}: {e}")
            return False
    
    def is_content_type_allowed(self, content_type):
        """Check if the content type is allowed for processing."""
        if not content_type:
            return True  # Allow unknown content types to be checked further
        
        # Extract main content type (ignore charset, etc.)
        main_type = content_type.split(';')[0].strip().lower()
        return main_type in self.ALLOWED_CONTENT_TYPES
    
    def detect_data_file_content(self, text, sample_size=1000):
        """Detect if content appears to be a data file rather than readable text."""
        # Take a sample of the text to analyze
        sample = text[:sample_size]
        
        # Check for common data file patterns
        data_patterns = [
            r'^\d+\s+\w+\s*$',  # Number followed by word (like frequency data)
            r'^\w+\s+\d+\s*$',  # Word followed by number
            r'^\d+,\d+',        # CSV-like data
            r'^\d+\t\w+',       # Tab-separated data
            r'^\w+:\d+',        # Key:value pairs
        ]
        
        lines = sample.split('\n')[:20]  # Check first 20 lines
        data_line_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            for pattern in data_patterns:
                if re.match(pattern, line):
                    data_line_count += 1
                    break
        
        # If more than 70% of lines match data patterns, it's likely a data file
        total_lines = len([l for l in lines if l.strip()])
        return total_lines > 0 and data_line_count > total_lines * 0.7
    
    def enhanced_has_proper_sentences(self, text):
        """Enhanced version of your has_proper_sentences function with additional validation."""
        if not text or len(text.strip()) < 50:
            return False
        
        # First check if it's a data file
        if self.detect_data_file_content(text):
            return False
        
        # Use your original logic
        from nltk.tokenize import sent_tokenize
        sentences = sent_tokenize(text)
        
        # Check for sentences that end with proper punctuation and have reasonable length
        proper_sentences = [s for s in sentences if s.strip().endswith(('.', '!', '?')) and len(s.split()) > 5]
        return len(proper_sentences) >= 2
    
    async def fetch_page(self, session, url, timeout=60):
        """Enhanced fetch_page function with content filtering."""
        # Pre-filter URLs
        if not self.should_process_url(url):
            return f"URL blocked by content filter: {url}", None
        
        headers = {
            'User-Agent': random.choice(USER_AGENTS)
        }
        
        # Create timeout object for both connection and read
        timeout_obj = aiohttp.ClientTimeout(total=timeout, connect=10, sock_read=timeout)
        
        try:
            async with session.get(url, headers=headers, timeout=timeout_obj) as response:
                content_type = response.headers.get('Content-Type', '')
                
                # Check if content type is allowed
                if not self.is_content_type_allowed(content_type):
                    response.release()
                    return f"Content type not allowed: {content_type}", None
                
                # Check content length to avoid very large files
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > 5_000_000:  # 5MB limit
                    response.release()
                    return f"Content too large: {content_length} bytes", None
                
                if 'text' in content_type:
                    encoding = response.charset or 'utf-8'
                    content = await response.text(encoding=encoding)
                    
                    # Additional content validation
                    if self.detect_data_file_content(content):
                        response.release()
                        return f"Content appears to be a data file, not suitable for summarization", None
                    
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

    async def process_page(self, session, url, semaphore, full_text=False):
        """Enhanced process_page function with better error handling and content validation."""
        async with semaphore:
            try:
                result = await self.fetch_page(session, url)
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
                elif isinstance(result, str) and not result.startswith(('Timeout error', 'Client error', 'SSL handshake error', 'Unexpected error', 'URL blocked', 'Content type not allowed', 'Content too large', 'Content appears to be')):
                    soup = BeautifulSoup(result, 'lxml')

                    elements_to_extract = ['p', 'li', 'summary', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'pre', 'td', 'th', 'a']

                    text = ' '.join(element.get_text().strip() for element in soup.find_all(elements_to_extract))
                    cleaned_text = clean_website_data(text)

                    # Enhanced validation before summarization
                    if not cleaned_text or len(cleaned_text.strip()) < 100:
                        response_list.append({
                            "type": "text",
                            "text": {
                                'url': url,
                                'error': 'Insufficient content for summarization'
                            }
                        })
                        return response_list

                    if full_text:
                        if self.enhanced_has_proper_sentences(cleaned_text):
                            summary_or_full_text = rank_sentences(cleaned_text, stopwords, max_sentences=20)  
                        else:
                            # Provide truncated content if no proper sentences
                            summary_or_full_text = cleaned_text[:1000] + "..." if len(cleaned_text) > 1000 else cleaned_text
                    else:
                        try:
                            if self.enhanced_has_proper_sentences(cleaned_text):
                                summary_or_full_text = rank_sentences(cleaned_text, stopwords, max_sentences=20) 
                            else:
                                # Provide truncated content if no proper sentences
                                summary_or_full_text = cleaned_text[:500] + "..." if len(cleaned_text) > 500 else cleaned_text
                        except Exception as e:
                            logging.error(f"Failed to rank sentences: {e}")
                            print(f"Failed to rank sentences for {url}: {e}")
                            summary_or_full_text = cleaned_text[:1000] + "..." if len(cleaned_text) > 1000 else cleaned_text

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

    async def get_web_pages(self, urls, full_text=False, max_concurrent_requests=5):
        """Enhanced get_web_pages function using the class methods."""
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
                tasks = [self.process_page(session, url, semaphore, full_text) for url in urls]
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
        finally:
            # Ensure connector is closed even if session context manager doesn't run
            if 'connector' in locals():
                await connector.close()

    def browse_internet(self, urls, full_text=False):
        """Enhanced browse_internet function - drop-in replacement."""
        try:
            # Suppress resource warnings in Lambda environment
            import warnings
            warnings.filterwarnings("ignore", category=ResourceWarning)
            
            web_pages = asyncio.run(self.get_web_pages(urls, full_text))
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


def upload_image_content_to_s3(image_content: bytes, mime_type: str) -> str:
    """
    Upload image content directly to S3 and return the S3 URL.
    Following the same pattern as upload_document_to_s3.
    
    Args:
        image_content (bytes): Binary image data
        mime_type (str): MIME type of the image (e.g., 'image/png')
    
    Returns:
        str: S3 URL of uploaded image
    """
    image_extension = mimetypes.guess_extension(mime_type) or '.bin'
    s3_object_name = f"Generated_Image_{datetime.datetime.now(datetime.UTC).strftime('%Y%m%d%H%M%S')}{image_extension}"
    
    # Upload to S3
    s3_client = boto3.client('s3')
    s3_client.put_object(Body=image_content, Bucket=image_bucket_name, Key=s3_object_name)
    
    # Construct the S3 URL
    s3_url = f"https://{image_bucket_name}.s3.amazonaws.com/{s3_object_name}"
    return s3_url


def gemini_generate_content(
    prompt: str,
    file_name_prefix: str = "generated_content",
    model: str = "gemini-2.5-flash-image-preview",
    input_images: list = None
) -> Dict[str, Any]:
    """
    Generate content using Google's Gemini API with support for both text and image outputs.
    Supports text-to-image generation and image editing (text-and-image-to-image).

    This function integrates with the existing system's Gemini API configuration and
    AWS S3 infrastructure for image storage.

    Args:
        prompt (str): The text prompt to send to Gemini
        file_name_prefix (str): Prefix for generated file names (default: "generated_content")
        model (str): Gemini model to use (default: "gemini-2.5-flash-image-preview")
        input_images (list): Optional list of input images for editing. Each item can be:
            - A URL string (will be downloaded and converted to base64)
            - A dict with 'data' (base64 string) and 'mime_type' keys
            - Max 3 images supported

    Returns:
        Dict[str, Any]: Dictionary containing:
            - "success": bool indicating if the operation was successful
            - "text_content": str containing all text responses
            - "generated_files": list of S3 URLs for saved images
            - "error": str containing error message if success is False
    """
    
    result = {
        "success": False,
        "text_content": "",
        "generated_files": [],
        "error": ""
    }
    
    try:
        # Use API key from config (already available in system)
        if not gemini_api_key:
            result["error"] = "Gemini API key not found in system configuration"
            return result
        
        # Prepare the API request (non-streaming version)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": gemini_api_key
        }
        
        # Prepare the parts array for the request
        parts = []

        # Add input images if provided (for image editing)
        if input_images:
            # Limit to 3 images as per Gemini API documentation
            for img in input_images[:3]:
                if isinstance(img, str):
                    # If it's a URL, download and convert to base64
                    try:
                        # Download image with Slack authorization if needed
                        headers = {}
                        if 'slack' in img:
                            headers = {'Authorization': f'Bearer {slack_bot_token}'}

                        img_response = requests.get(img, headers=headers, timeout=30)
                        img_response.raise_for_status()

                        # Convert to base64
                        img_data = base64.b64encode(img_response.content).decode('utf-8')

                        # Determine mime type
                        content_type = img_response.headers.get('Content-Type', 'image/png')
                        mime_type = content_type.split(';')[0].strip()

                        parts.append({
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": img_data
                            }
                        })
                    except Exception as e:
                        result["error"] = f"Failed to download input image from {img}: {str(e)}"
                        return result

                elif isinstance(img, dict) and 'data' in img and 'mime_type' in img:
                    # If it's already a dict with base64 data
                    parts.append({
                        "inline_data": {
                            "mime_type": img['mime_type'],
                            "data": img['data']
                        }
                    })

        # Add the text prompt
        parts.append({
            "text": prompt
        })

        # Prepare the request payload
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": parts
                }
            ],
            "generationConfig": {
                "response_modalities": ["IMAGE", "TEXT"],
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 8192
            }
        }
        
        # Make the request
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code != 200:
            result["error"] = f"API request failed with status {response.status_code}: {response.text}"
            return result
        
        response_data = response.json()
        
        # Process the response
        file_index = 0
        text_parts = []
        
        if 'candidates' in response_data and response_data['candidates']:
            candidate = response_data['candidates'][0]
            
            if 'content' in candidate and 'parts' in candidate['content']:
                parts = candidate['content']['parts']
                
                for part in parts:
                    # Handle inline data (images)
                    if 'inlineData' in part:
                        inline_data = part['inlineData']
                        if 'data' in inline_data:
                            # Decode base64 data
                            try:
                                data_buffer = base64.b64decode(inline_data['data'])
                                mime_type = inline_data.get('mimeType', 'image/png')
                                
                                # Upload to S3 using our helper function
                                s3_url = upload_image_content_to_s3(data_buffer, mime_type)
                                result["generated_files"].append(s3_url)
                                file_index += 1
                                
                            except Exception as e:
                                print(f"Error processing image data: {str(e)}")
                    
                    # Handle text data
                    elif 'text' in part:
                        text_content = part['text']
                        text_parts.append(text_content)
        
        # Combine all text content
        result["text_content"] = "".join(text_parts)
        result["success"] = True
        
        print(f"Generation completed successfully!")
        print(f"Text content length: {len(result['text_content'])} characters")
        print(f"Files generated: {len(result['generated_files'])}")
        
    except requests.exceptions.Timeout:
        result["error"] = "Request timed out. The generation may have taken too long."
    except requests.exceptions.RequestException as e:
        result["error"] = f"Request error: {str(e)}"
    except Exception as e:
        result["error"] = f"Error during content generation: {str(e)}"
        print(f"Error: {result['error']}")
    
    return result
