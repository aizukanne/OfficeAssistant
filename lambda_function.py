import aiohttp
import asyncio
import base64
import boto3
import calendar
import concurrent.futures
import csv
import datetime
import json
import logging
import markdown2
import mimetypes
import nltk
import openai
import openpyxl
import os
import PyPDF2
import random
import re
import requests
import tempfile
import textwrap
import time
import wave
import weaviate
import weaviate.classes as wvc
import zipfile

from amazon_functions import search_amazon_products, format_product_results, search_and_format_products
from aiohttp.client_exceptions import ClientConnectorSSLError
from boto3.dynamodb.conditions import Key
from botocore.exceptions import NoCredentialsError
from botocore.exceptions import ClientError
from bs4 import BeautifulSoup
from bson import ObjectId
from collections import Counter
from datetime import timedelta, UTC
from decimal import Decimal
from docx import Document
from html.parser import HTMLParser
from io import BytesIO, StringIO
from odoo_functions import authenticate, odoo_get_mapped_models, odoo_get_mapped_fields, odoo_create_record, odoo_fetch_records, odoo_update_record, odoo_delete_record, odoo_print_record, odoo_post_record
from openai import OpenAIError, BadRequestError
from prompts import prompts  # Import the prompts from prompts.py
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, Line
from reportlab.graphics import renderPDF
from semantic_router import Route
from semantic_router import RouteLayer
from semantic_router.encoders import OpenAIEncoder
from tools import tools #Import tools from tools.py
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urlparse, unquote, quote_plus, urlencode, urljoin
from urllib.request import urlopen
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
from weaviate.classes.query import Sort
from xml.etree import ElementTree

from config import *  # Import all configuration variables
from parallel_utils import ParallelExecutor, time_operation, time_operation_with_metrics, log_performance_data
from parallel_storage import (
    get_message_history_parallel,
    get_relevant_messages_parallel,
    parallel_preprocessing
)
from storage_pooled import init_weaviate_pool, get_pool_statistics

# Initialize Weaviate connection pool at module level
print("Initializing Weaviate connection pool...")
init_weaviate_pool(pool_size=5, max_overflow=2)
from extservices import get_coordinates
from extservices import get_weather_data
from nltk.tokenize import sent_tokenize, word_tokenize

from conversation import (
    make_text_conversation, make_vision_conversation, make_audio_conversation, make_cerebras_conversation,
    make_openai_vision_call, make_openai_audio_call, ask_openai_o1, make_openrouter_call,
    serialize_chat_completion_message, handle_message_content, handle_tool_calls
)

from media_processing import (
    text_to_speech, upload_image_to_s3, transcribe_speech_from_memory,
    download_audio_to_memory, process_url, transcribe_multiple_urls,
    convert_to_wav_in_memory, has_proper_sentences
)

from nlp_utils import (
    load_stopwords, rank_sentences, summarize_record, summarize_messages,
    clean_website_data, detect_pii
)

from slack_integration import (
    send_slack_message, send_audio_to_slack, send_file_to_slack,
    get_slack_user_name, update_slack_users, update_slack_conversations,
    find_image_urls, latex_to_slack, message_to_json, process_slack_event,
    send_typing_indicator, set_slack_channel_description, create_slack_channel,
    invite_users_to_slack_channel
)

from storage import (
    save_message_weaviate, get_last_messages_weaviate, 
    get_relevant_messages, save_message, get_last_messages,
    get_message_by_sort_id, get_messages_in_range, get_users, 
    get_channels, manage_mute_status
)

from telegram_integration import (
    process_telegram_event, send_telegram_message, send_telegram_audio, send_telegram_file
)

nltk.data.path.append("/opt/python/nltk_data")

def get_available_functions(source):
    """
    Get available functions based on the source platform.
    
    Args:
        source (str): The platform source ('slack', 'telegram', etc.)
        
    Returns:
        dict: Dictionary of available functions for the platform
    """
    # Common functions available to all platforms
    common_functions = {
        "browse_internet": browse_internet,
        "google_search": google_search,
        "get_coordinates": get_coordinates,
        "get_weather_data": get_weather_data,
        "get_message_by_sort_id": get_message_by_sort_id,
        "get_messages_in_range": get_messages_in_range,
        "get_users": get_users,
        "get_channels": get_channels,
        "send_as_pdf": send_as_pdf,
        "list_files": list_files,
        "solve_maths": solve_maths,
        "odoo_get_mapped_models": odoo_get_mapped_models,
        #"odoo_get_mapped_fields": odoo_get_mapped_fields,
        "odoo_create_record": odoo_create_record,
        "odoo_fetch_records": odoo_fetch_records,
        "odoo_update_record": odoo_update_record,
        "odoo_delete_record": odoo_delete_record,
        "odoo_print_record": odoo_print_record,
        "odoo_post_record": odoo_post_record,
        "ask_openai_o1": ask_openai_o1,
        "get_embedding": get_embedding,
        "manage_mute_status": manage_mute_status,
        "search_and_format_products": search_and_format_products
    }
    
    # Platform-specific functions
    if source == 'slack':
        platform_functions = {
            "send_slack_message": send_slack_message,
            "send_audio_to_slack": send_audio_to_slack,
            "send_file_to_slack": send_file_to_slack,
            "set_slack_channel_description": set_slack_channel_description,
            "create_slack_channel": create_slack_channel,
            "invite_users_to_slack_channel": invite_users_to_slack_channel
        }
    elif source == 'telegram':
        platform_functions = {
            "send_telegram_message": send_telegram_message,
            "send_telegram_audio": send_telegram_audio,
            "send_telegram_file": send_telegram_file,
        }
    else:
        # Default to no platform-specific functions for unknown sources
        platform_functions = {}
    
    # Combine common and platform-specific functions
    all_functions = {**common_functions, **platform_functions}
    
    print(f"Loaded {len(all_functions)} functions for platform '{source}' ({len(common_functions)} common + {len(platform_functions)} platform-specific)")
    
    return all_functions

# Any remaining global variables that need to stay in the main file
current_datetime = datetime.datetime.now(UTC)

# Connect to Weaviate Cloud
weaviate_client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
    headers = headers
)


@time_operation_with_metrics("lambda_handler_total")
def lambda_handler(event, context):
    print(f"Event: {event}")
    
    # Periodically log connection pool statistics (10% of invocations)
    if random.random() < 0.1:
        try:
            pool_stats = get_pool_statistics()
            print(f"Weaviate connection pool stats: {json.dumps(pool_stats)}")
        except Exception as e:
            print(f"Error getting pool stats: {e}")
    
    global stopwords
    global chat_id
    global user_id
    global thread_ts
    global audio_text
    global conversation
    global source

    stopwords = load_stopwords('english')
    has_image = ''
    audio_text = ''
    has_audio = False
    image_urls = []   
    has_image_urls = False
    relevant = 5
    models = {}

    rl = RouteLayer.from_json("routes_layer.json")

    # Get route (common processing)
    route_name = ""    
    
    
    if 'Records' in event and isinstance(event['Records'], list):
        source = "email"
        payload = event['Records'][0]['body']
        body_str = json.loads(payload)['payload']['event']
        event_type = body_str['type']
        #print(f"Mail Body: {body_str}")
        system_text = prompts['system_text']
        email_instructions = prompts['email_instructions']

        # Get the current time as a Unix timestamp with fractional seconds    
        timestamp = time.time()
        
        # Format the timestamp as a string with 6 decimal places   
        thread_ts = f"{timestamp:.6f}"
        #print(f"Thread_ts: {thread_ts}")
        chat_id = "C06QL84KZGQ"
        user_id = "U02RPR2RMJS"
        
        user = get_users(user_id)
        user_name = user['real_name']
        display_name = user['display_name']
        display_name = display_name.replace(' ', '_').replace('.', '').strip()
        text = f"Email: {body_str} "
        print(text)
        conversation = make_vision_conversation(system_text, email_instructions,  display_name, '', '', '', text)
        response_message = make_openai_vision_call(client, conversation)
        
    else:
        body_str = event.get('body', '{}')
        print(f"Body: {body_str}")
        
        enable_pii = False
        
        # Parse the incoming event
        parsed_body = json.loads(body_str)
        
        # Detect source and process accordingly
        source = event.get('source', 'slack')  # Default to slack for backward compatibility
        
        if source == 'telegram':
            print("Processing Telegram event")
            processed_data = process_telegram_event(parsed_body)
        else:
            # Default to Slack processing (for backward compatibility)
            print("Processing Slack event")
            processed_data = process_slack_event(parsed_body)
        
        # Check if processing was successful
        if processed_data is None:
            print("Event processing failed or should be ignored")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Ignored message.'})
            }
        
        # Extract processed parameters
        chat_id = processed_data['chat_id']
        thread_ts = processed_data['thread_ts']

        # REFRESH TYPING INDICATOR - since we're in the backend now
        if source == 'slack':
            print(f"Starting typing indication for channel {chat_id}") 
            send_typing_indicator(chat_id, duration=60, method="simulation")

        user_id = processed_data['user_id']
        user_name = processed_data['user_name']
        display_name = processed_data['display_name']
        text = processed_data['text']
        image_urls = processed_data['image_urls']
        audio_urls = processed_data['audio_urls']
        audio_text = processed_data['audio_text']
        application_files = processed_data['application_files']
        event_type = processed_data['event_type']
        
        print(f"Processed {source} event - Chat ID: {chat_id}, User: {user_name}, Text: {text[:50]}...")
        
        # Append audio transcriptions and file contents to text (for both platforms)
        if audio_text:
            combined_audio_text = ' '.join(audio_text)
            text += f" {combined_audio_text}"
            print(f"Added audio transcription to text: {combined_audio_text[:100]}...")
        
        if application_files:
            files_json = json.dumps(application_files)
            text += f" {files_json}"
            print(f"Added application files to text: {len(application_files)} files")
        
        if text:
            try:
                route_choice = rl(text)
                print(f'Route Choice: {route_choice}')
                route_name = route_choice.name
            except ValueError as e:
                if "maximum context length" in str(e):
                    print(f"Warning: Text exceeds maximum context length. Using fallback routing. Error: {e}")
                    route_name = "chitchat"
                else:
                    raise
            except Exception as e:
                print(f"Error in routing: {e}")
                route_name = "unknown_route"

        # Retrieve the last N messages from the user and assistant     
        if route_name == 'chitchat':
            summary_len = 0
            full_text_len = 2
            relevant = 2
            system_text = prompts['instruct_basic']
            assistant_text = ""
        elif route_name == 'writing':
            system_text = prompts['system_text']
            assistant_text = prompts['assistant_text'] + " " + prompts['instruct_writing']
            summary_len = 10
            full_text_len = 5 
        elif route_name == 'odoo_erp':
            system_text = prompts['system_text']
            assistant_text = prompts['assistant_text'] + " " + prompts['odoo_search'] + " " + prompts['instruct_Context_Clarification']
            summary_len = 2
            full_text_len = 5
            relevant = 0
            ai_temperature = 0.1   
        else:
            system_text = prompts['system_text']
            assistant_text = prompts['assistant_text'] + " " + prompts['odoo_search'] + " " + prompts['instruct_Context_Clarification'] + " " + prompts['instruct_chain_of_thought']
            summary_len = 10
            full_text_len = 5

        num_messages = summary_len + full_text_len  # or any other number you prefer

        # Log start of parallel processing
        parallel_start_time = time.time()
        
        # PARALLEL EXECUTION PHASE 1: Message History & Initial Processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit parallel tasks
            history_future = executor.submit(
                get_message_history_parallel,
                chat_id, num_messages, full_text_len
            )
            
            # Prepare preprocessing parameters
            enable_odoo = route_name == 'odoo_erp'
            
            preprocess_future = executor.submit(
                parallel_preprocessing,
                chat_id, text, route_name, relevant, enable_odoo
            )
            
            # Get results
            msg_history, all_messages, user_messages, assistant_messages = history_future.result()
            preprocess_results = preprocess_future.result()
        
        # Log parallel processing time
        parallel_duration = (time.time() - parallel_start_time) * 1000
        log_performance_data("parallel_processing_phase1", parallel_duration, {
            "route": route_name,
            "chat_id": chat_id,
            "num_messages": num_messages
        })
        
        # Extract preprocessing results
        maria_muted = preprocess_results.get('mute_status', [False])[0] if preprocess_results.get('mute_status') else False
        models = preprocess_results.get('odoo_models', {})
        all_relevant_messages = preprocess_results.get('relevant_messages', [])
        
        # Handle mute status
        try:
            match_id = re.search(r"<@(\w+)>", text)
            mentioned_user_id = match_id.group(1) if match_id else None
            print(f"Maria muted: {maria_muted}")
            # Check if Maria is muted and the mentioned user is not the specified ID
            if maria_muted and mentioned_user_id != "U05SSQR07RS":
                print("We are in the Maria is muted IF...")
                save_message(meetings_table, chat_id, text, "user", thread_ts, image_urls)
                return  # Exit the function after saving the message
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        
        # Summarize message history
        msg_history_summary = [summarize_messages(msg_history)]
        
        # Find image URLs
        has_image_urls, all_image_urls = find_image_urls(all_messages)
        
        # PII detection if enabled
        if enable_pii:
            text = detect_pii(text)

        if has_audio:
            # Use audio conversation for audio inputs
            conversation = make_audio_conversation(system_text, assistant_text, display_name, 
                                                all_relevant_messages, msg_history_summary, 
                                                all_messages, text, models, audio_urls)
            # Use the audio-specific model
            response_message = make_openai_audio_call(client, conversation)
        elif image_urls or has_image_urls:
            # Keep the existing vision conversation path for images
            conversation = make_vision_conversation(system_text, assistant_text, display_name, 
                                                all_relevant_messages, msg_history_summary, 
                                                all_messages, text, models, image_urls)
            response_message = make_openai_vision_call(client, conversation)
        else:
            if route_name == 'chitchat':
                # Regular vision conversation for text-only
                conversation = make_cerebras_conversation(system_text, assistant_text, display_name, all_relevant_messages, msg_history_summary, all_messages, text, models)
                response_message = make_openrouter_call(openrouter_client, conversation)
            else:
                conversation = make_vision_conversation(system_text, assistant_text, display_name, all_relevant_messages, msg_history_summary, all_messages, text, models)
                response_message = make_openai_vision_call(client, conversation)

    # Save the user's message to Database 
    save_message_weaviate(user_table, chat_id, text, thread_ts, image_urls)

    # Define available functions dynamically based on source platform
    available_functions = get_available_functions(source)

    while True:
        # Handle message content if present
        if isinstance(response_message, dict):
            has_content = response_message.get("content")
            has_audio = response_message.get("audio")
            has_tool_calls = response_message.get("tool_calls")
        else:
            has_content = getattr(response_message, "content", None)
            has_audio = getattr(response_message, "audio", None)
            has_tool_calls = getattr(response_message, "tool_calls", None)

        if has_content or has_audio:
            handle_message_content(response_message, event_type, thread_ts, chat_id, audio_text, source)

        # Check and process tool calls
        if has_tool_calls:
            # REFRESH TYPING for tool processing
            if source == 'slack' and chat_id:
                send_typing_indicator(chat_id, duration=20)

            conversation_with_tool_responses = handle_tool_calls(
                response_message, available_functions, chat_id, conversation, thread_ts
            )

            if has_audio:
                # Make sure to use the audio call for continued conversation
                response_message = make_openai_audio_call(client, conversation_with_tool_responses)
            elif image_urls or has_image_urls:
                # Use vision for image-based conversations
                response_message = make_openai_vision_call(client, conversation_with_tool_responses)
            else:
                if route_name == 'chitchat':
                    response_message = make_openrouter_call(openrouter_client, conversation_with_tool_responses)
                else:
                    response_message = make_openai_vision_call(client, conversation_with_tool_responses)
        else:

            weaviate_client.close()
            break  # Exit the loop if there are no tool calls


# Function to convert non-serializable types for JSON serialization  
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, ObjectId):
        return str(obj)  # Convert ObjectId to string
    raise TypeError("Unserializable object {} of type {}".format(obj, type(obj)))
    

def convert_floats_to_decimals(obj):
    if isinstance(obj, float):
        return decimal.Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimals(v) for v in obj]
    return obj
    
    
def get_embedding(text, model="text-embedding-ada-002"):
    text_cleaned = text.replace("\n", " ")
    embedding = client.embeddings.create(input=[text_cleaned], model=model).data[0].embedding
    return {"text": text_cleaned, "embedding": embedding}
    

def send_to_sqs(data, queue_url):
    sqs = boto3.client('sqs')
    payload = {
        'payload': data
    }
    
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(payload)
    )

def invoke_lambda(data):
    lambda_client = boto3.client('lambda')
    payload = {
        'payload': data
    }
    response = lambda_client.invoke(
        FunctionName='cerenyiWebsearch',
        InvocationType='RequestResponse',  # Changed to synchronous invocation
        Payload=json.dumps(payload),
    )
    
    # To get the response payload   
    response_payload = json.loads(response['Payload'].read())
    return response_payload


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
    finally:
        # Ensure connector is closed even if session context manager doesn't run
        if 'connector' in locals():
            await connector.close()


async def fetch_page(session, url, timeout=60):
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

                if full_text:
                    if has_proper_sentences(cleaned_text):
                        summary_or_full_text = rank_sentences(cleaned_text, stopwords, max_sentences=50)  
                    else:
                        summary_or_full_text = cleaned_text
                else:
                    try:
                        if has_proper_sentences(cleaned_text):
                            summary_or_full_text = rank_sentences(cleaned_text, stopwords, max_sentences=20) 
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

def upload_document_to_s3(document_content, content_type, document_url):
    document_extension = mimetypes.guess_extension(content_type) or '.bin'
    s3_object_name = f"Document_{datetime.datetime.now(datetime.UTC).strftime('%Y%m%d%H%M%S')}{document_extension}"

    # Upload to S3   
    s3_client = boto3.client('s3')
    s3_client.put_object(Body=document_content, Bucket=docs_bucket_name, Key=s3_object_name)

    # Construct the S3 URL  
    s3_url = f"https://{docs_bucket_name}.s3.amazonaws.com/{s3_object_name}"
    return s3_url


def smart_send_message(message, user_name):
    users = get_users()  # Assume this function returns a list of user dictionaries  
    matched_users = []
    similar_users = []

    for user in users:
        names = [user.get('real_name', ''), user.get('display_name', '')]
        for name in names:
            if user_name.lower() == name.lower():
                matched_users.append(user)
            elif user_name.lower() in name.lower().split():
                similar_users.append(user)

    if len(matched_users) == 1:
        user_id = matched_users[0]['user_id']
        send_slack_message(user_id, message, None)
        return f"Message sent to {matched_users[0]['real_name']} ({matched_users[0]['display_name']})."
    elif len(matched_users) > 1:
        return "Multiple matches found. Please confirm the user: " + ", ".join([f"{u['real_name']} ({u['display_name']})" for u in matched_users])
    elif similar_users:
        return "No exact match found. Did you mean: " + ", ".join([f"{u['real_name']} ({u['display_name']})" for u in similar_users]) + "?"
    else:
        return "No matching user found."


class BeautifulPDFGenerator:
    def __init__(self, title, page_size=letter, theme='professional'):
        self.title = title
        self.page_size = page_size
        self.theme = theme
        self.styles = getSampleStyleSheet()
        self.story = []
        self.themes = {
            'professional': {
                'primary_color': colors.HexColor('#2C3E50'),
                'accent_color': colors.HexColor('#3498DB'),
                'text_color': colors.HexColor('#2C3E50'),
                'light_gray': colors.HexColor('#ECF0F1'),
                'dark_gray': colors.HexColor('#7F8C8D')
            },
            'modern': {
                'primary_color': colors.HexColor('#1A1A1A'),
                'accent_color': colors.HexColor('#FF6B6B'),
                'text_color': colors.HexColor('#333333'),
                'light_gray': colors.HexColor('#F8F9FA'),
                'dark_gray': colors.HexColor('#6C757D')
            },
            'corporate': {
                'primary_color': colors.HexColor('#0F4C75'),
                'accent_color': colors.HexColor('#3282B8'),
                'text_color': colors.HexColor('#2C3E50'),
                'light_gray': colors.HexColor('#E8F4FD'),
                'dark_gray': colors.HexColor('#5A6C7D')
            }
        }
        self._setup_beautiful_styles()
    
    def _setup_beautiful_styles(self):
        """Setup beautiful, professional paragraph styles"""
        theme_colors = self.themes.get(self.theme, self.themes['professional'])
        
        # Title page style
        self.styles.add(ParagraphStyle(
            name='DocumentTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=theme_colors['primary_color'],
            fontName='Helvetica-Bold'
        ))
        
        # Section headers with colored background
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceBefore=25,
            spaceAfter=15,
            textColor=colors.white,
            fontName='Helvetica-Bold',
            backColor=theme_colors['primary_color'],
            borderPadding=10,
            leftIndent=10,
            rightIndent=10
        ))
        
        # Subsection headers
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=12,
            textColor=theme_colors['accent_color'],
            fontName='Helvetica-Bold',
            borderWidth=0,
            borderColor=theme_colors['accent_color'],
            borderPadding=5,
            leftIndent=5
        ))
        
        # Minor headers
        self.styles.add(ParagraphStyle(
            name='MinorHeader',
            parent=self.styles['Heading3'],
            fontSize=13,
            spaceBefore=15,
            spaceAfter=10,
            textColor=theme_colors['primary_color'],
            fontName='Helvetica-Bold'
        ))
        
        # Body text with tighter spacing
        self.styles.add(ParagraphStyle(
            name='BeautifulBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceBefore=4,
            spaceAfter=4,
            alignment=TA_JUSTIFY,
            leading=14,
            textColor=theme_colors['text_color'],
            fontName='Helvetica'
        ))
        
        # SCQA section headers renamed to SectionHeader for any bold text ending with colon
        self.styles.add(ParagraphStyle(
            name='SCQAHeader',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6,
            alignment=TA_LEFT,
            leading=14,
            textColor=theme_colors['primary_color'],
            fontName='Helvetica-Bold'
        ))
        
        # Enhanced list style with tighter spacing
        self.styles.add(ParagraphStyle(
            name='BeautifulBullet',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceBefore=2,
            spaceAfter=2,
            leftIndent=25,
            bulletIndent=15,
            leading=14,
            textColor=theme_colors['text_color'],
            fontName='Helvetica'
        ))
        
        # Quote/callout style with tighter spacing
        self.styles.add(ParagraphStyle(
            name='Callout',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceBefore=8,
            spaceAfter=8,
            leftIndent=20,
            rightIndent=20,
            alignment=TA_JUSTIFY,
            leading=14,
            textColor=theme_colors['text_color'],
            backColor=theme_colors['light_gray'],
            borderColor=theme_colors['accent_color'],
            borderWidth=1,
            borderPadding=10,
            fontName='Helvetica-Oblique'
        ))
        
        # Metadata/footer style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceBefore=15,
            spaceAfter=3,
            alignment=TA_RIGHT,
            textColor=theme_colors['dark_gray'],
            fontName='Helvetica-Oblique'
        ))

    def _create_header_footer_canvas(self, canvas_obj, doc):
        """Beautiful header and footer with styling"""
        canvas_obj.saveState()
        theme_colors = self.themes.get(self.theme, self.themes['professional'])
        
        # Header with colored line
        canvas_obj.setStrokeColor(theme_colors['accent_color'])
        canvas_obj.setLineWidth(2)
        header_y = doc.height + doc.topMargin - 0.3 * inch
        canvas_obj.line(doc.leftMargin, header_y, doc.width + doc.leftMargin, header_y)
        
        # Header text
        canvas_obj.setFont('Helvetica-Bold', 11)
        canvas_obj.setFillColor(theme_colors['primary_color'])
        x_center = doc.width / 2 + doc.leftMargin
        
        if hasattr(canvas_obj, 'drawCentredText'):
            canvas_obj.drawCentredText(x_center, header_y + 15, self.title)
        else:
            text_width = canvas_obj.stringWidth(self.title, 'Helvetica-Bold', 11)
            canvas_obj.drawString(x_center - text_width/2, header_y + 15, self.title)
        
        # Footer with styled page numbers
        canvas_obj.setStrokeColor(theme_colors['accent_color'])
        canvas_obj.setLineWidth(1)
        footer_y = doc.bottomMargin - 0.5 * inch
        canvas_obj.line(doc.leftMargin, footer_y + 15, doc.width + doc.leftMargin, footer_y + 15)
        
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.setFillColor(theme_colors['dark_gray'])
        footer_text = f'Page {canvas_obj.getPageNumber()}'
        
        if hasattr(canvas_obj, 'drawCentredText'):
            canvas_obj.drawCentredText(x_center, footer_y, footer_text)
        else:
            text_width = canvas_obj.stringWidth(footer_text, 'Helvetica', 9)
            canvas_obj.drawString(x_center - text_width/2, footer_y, footer_text)
        
        canvas_obj.restoreState()

    def add_title_page(self):
        """Add a beautiful title page"""
        theme_colors = self.themes.get(self.theme, self.themes['professional'])
        
        # Add some space
        self.story.append(Spacer(1, 2*inch))
        
        # Main title
        title_para = Paragraph(self.title, self.styles['DocumentTitle'])
        self.story.append(title_para)
        
        # Decorative line
        line_drawing = Drawing(400, 20)
        line_drawing.add(Line(0, 10, 400, 10, strokeColor=theme_colors['accent_color'], strokeWidth=3))
        self.story.append(line_drawing)
        
        self.story.append(Spacer(1, 1*inch))
        
    def add_image(self, image_path_or_url, width=None, height=None, caption=None):
        """Add an image to the document with optional caption"""
        try:
            # Handle URLs
            if image_path_or_url.startswith(('http://', 'https://')):
                response = urlopen(image_path_or_url)
                image_data = BytesIO(response.read())
                img = Image(image_data)
            # Handle base64 encoded images
            elif image_path_or_url.startswith('data:image'):
                header, data = image_path_or_url.split(',', 1)
                image_data = BytesIO(base64.b64decode(data))
                img = Image(image_data)
            # Handle local file paths
            else:
                img = Image(image_path_or_url)
            
            # Set dimensions
            if width and height:
                img.drawWidth = width
                img.drawHeight = height
            elif width:
                img.drawWidth = width
                img.drawHeight = img.drawHeight * (width / img.drawWidth)
            elif height:
                img.drawHeight = height
                img.drawWidth = img.drawWidth * (height / img.drawHeight)
            else:
                # Default max width
                max_width = 5*inch
                if img.drawWidth > max_width:
                    img.drawHeight = img.drawHeight * (max_width / img.drawWidth)
                    img.drawWidth = max_width
            
            # Center the image
            img.hAlign = 'CENTER'
            
            self.story.append(Spacer(1, 10))
            self.story.append(img)
            
            # Add caption if provided
            if caption:
                caption_style = ParagraphStyle(
                    'ImageCaption',
                    parent=self.styles['Normal'],
                    fontSize=9,
                    spaceAfter=15,
                    alignment=TA_CENTER,
                    textColor=self.themes[self.theme]['dark_gray'],
                    fontName='Helvetica-Oblique'
                )
                self.story.append(Paragraph(f"<i>{caption}</i>", caption_style))
            else:
                self.story.append(Spacer(1, 10))
                
        except Exception as e:
            # If image fails to load, add an error message
            error_para = Paragraph(f"[Image could not be loaded: {str(e)}]", self.styles['BeautifulBody'])
            self.story.append(error_para)

    def write_html(self, html_content):
        """Convert HTML content to beautiful ReportLab story elements"""
        parser = BeautifulHTMLParser(self.styles, self)
        parser.feed(html_content)
        self.story.extend(parser.get_story())

    def generate_pdf(self, output_path):
        """Generate the beautiful PDF file"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.page_size,
            rightMargin=0.8*inch,
            leftMargin=0.8*inch,
            topMargin=1.2*inch,
            bottomMargin=1*inch
        )
        
        # Build the PDF with custom canvas for headers/footers
        doc.build(
            self.story, 
            onFirstPage=self._create_header_footer_canvas,
            onLaterPages=self._create_header_footer_canvas
        )


class BeautifulHTMLParser(HTMLParser):
    """Enhanced HTML parser with image support and beautiful formatting"""
    
    def __init__(self, styles, pdf_generator):
        super().__init__()
        self.styles = styles
        self.pdf_generator = pdf_generator
        self.story = []
        self.current_text = ""
        self.tag_stack = []
        self.list_level = 0
        self.in_strong_section = False
        
    def handle_starttag(self, tag, attrs):
        self.tag_stack.append((tag, dict(attrs)))
        
        # Handle images
        if tag == 'img':
            self._flush_current_text()
            attrs_dict = dict(attrs)
            src = attrs_dict.get('src', '')
            alt = attrs_dict.get('alt', '')
            width = attrs_dict.get('width')
            height = attrs_dict.get('height')
            
            if width:
                width = float(width.replace('px', '')) if 'px' in str(width) else float(width)
            if height:
                height = float(height.replace('px', '')) if 'px' in str(height) else float(height)
                
            self.pdf_generator.add_image(src, width, height, alt if alt else None)
            return
        
        # Don't flush text for inline formatting tags
        if tag in ['h1', 'h2', 'h3', 'p', 'ul', 'ol', 'blockquote', 'hr']:
            self._flush_current_text()
            
        if tag == 'hr':
            # Add a horizontal rule
            theme_colors = self.pdf_generator.themes.get(self.pdf_generator.theme, self.pdf_generator.themes['professional'])
            line_drawing = Drawing(400, 10)
            line_drawing.add(Line(0, 5, 400, 5, strokeColor=theme_colors['accent_color'], strokeWidth=1))
            self.story.append(line_drawing)
            self.story.append(Spacer(1, 10))
            
        if tag in ['ul', 'ol']:
            self.list_level += 1
            
    def handle_endtag(self, tag):
        if self.tag_stack and self.tag_stack[-1][0] == tag:
            self.tag_stack.pop()
            
        if tag in ['h1', 'h2', 'h3', 'p', 'li', 'blockquote']:
            self._flush_current_text(tag)
            
        if tag in ['ul', 'ol']:
            self.list_level = max(0, self.list_level - 1)
            
        if tag in ['strong', 'b']:
            self.in_strong_section = False
            
    def handle_data(self, data):
        self.current_text += data
        
    def _flush_current_text(self, end_tag=None):
        """Convert accumulated text to appropriate beautiful paragraph style"""
        if not self.current_text.strip():
            self.current_text = ""
            return
            
        text = self.current_text.strip()
        
        # Check for section headers (any bold text ending with colon) BEFORE applying formatting
        is_section_header = False
        if ('strong' in [tag for tag, _ in self.tag_stack] or 'b' in [tag for tag, _ in self.tag_stack]):
            if text.endswith(':'):
                is_section_header = True
        
        formatted_text = self._apply_beautiful_formatting(text)
        
        # Determine style based on current context
        if 'h1' in [tag for tag, _ in self.tag_stack] or end_tag == 'h1':
            style = self.styles['SectionHeader']
        elif 'h2' in [tag for tag, _ in self.tag_stack] or end_tag == 'h2':
            style = self.styles['SubsectionHeader']
        elif 'h3' in [tag for tag, _ in self.tag_stack] or end_tag == 'h3':
            style = self.styles['MinorHeader']
        elif is_section_header:
            style = self.styles['SCQAHeader']
        elif 'blockquote' in [tag for tag, _ in self.tag_stack] or end_tag == 'blockquote':
            style = self.styles['Callout']
        elif 'li' in [tag for tag, _ in self.tag_stack] or end_tag == 'li':
            style = self.styles['BeautifulBullet']
            formatted_text = f"• {formatted_text}"
        else:
            # Check if this looks like metadata (prepared by, date, etc.)
            if any(keyword in text.lower() for keyword in ['prepared by:', 'date:', 'author:', 'version:']):
                style = self.styles['Metadata']
            else:
                style = self.styles['BeautifulBody']
            
        if formatted_text:
            para = Paragraph(formatted_text, style)
            
            # Add some special handling for section breaks
            if '---' in text:
                theme_colors = self.pdf_generator.themes.get(self.pdf_generator.theme, self.pdf_generator.themes['professional'])
                line_drawing = Drawing(400, 20)
                line_drawing.add(Line(50, 10, 350, 10, strokeColor=theme_colors['accent_color'], strokeWidth=2))
                self.story.append(Spacer(1, 8))
                self.story.append(line_drawing)
                self.story.append(Spacer(1, 8))
            else:
                self.story.append(para)
            
        self.current_text = ""
        
    def _apply_beautiful_formatting(self, text):
        """Apply beautiful inline formatting"""
        formatted_text = text
        
        # Apply formatting based on tag stack
        for tag, attrs in self.tag_stack:
            if tag in ['strong', 'b']:
                # Don't double-wrap if already wrapped
                if not formatted_text.startswith('<b>'):
                    formatted_text = f"<b>{formatted_text}</b>"
            elif tag in ['em', 'i']:
                # Don't double-wrap if already wrapped  
                if not formatted_text.startswith('<i>'):
                    formatted_text = f"<i>{formatted_text}</i>"
                
        return formatted_text
        
    def get_story(self):
        self._flush_current_text()
        return self.story


def clean_unicode_text(text):
    """Enhanced Unicode cleaning with more characters"""
    replacements = {
        # Quotation marks
        '\u2018': "'", '\u2019': "'", '\u201a': ",", '\u201b': "'",
        '\u201c': '"', '\u201d': '"', '\u201e': ',,', '\u201f': '"',
        
        # Dashes and hyphens
        '\u2013': '–', '\u2014': '—', '\u2010': '-', '\u2012': '-',
        '\u2015': '———', '\u2053': '~',
        
        # Spaces and breaks
        '\u00A0': ' ', '\u2000': ' ', '\u2001': ' ', '\u2002': ' ',
        '\u2003': ' ', '\u2004': ' ', '\u2005': ' ', '\u2006': ' ',
        '\u2007': ' ', '\u2008': ' ', '\u2009': ' ', '\u200A': ' ',
        '\u200B': '', '\u200C': '', '\u200D': '',
        
        # Symbols
        '\u2022': '•', '\u2023': '‣', '\u2024': '.', '\u2025': '..',
        '\u2026': '…', '\u2027': '‧', '\u2122': '™', '\u00A9': '©',
        '\u00AE': '®', '\u2120': '℠',
    }
    
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)
    
    return text


def send_as_pdf(text, chat_id, title, ts=None, theme='professional', include_title_page=False):
    """
    Beautiful PDF generator with image support - Drop-in replacement for the original function.
    
    Args:
        text (str): Markdown formatted text to convert to PDF
        chat_id (str): Slack channel ID
        title (str): PDF title and filename
        ts (str, optional): Slack thread timestamp
        theme (str, optional): Theme for styling ('professional', 'modern', 'corporate')
        include_title_page (bool, optional): Whether to include a title page
    
    Returns:
        str: Status message indicating success or failure
    """
    pdf_path = f"/tmp/{title}.pdf"
    
    try:
        # Clean the input text but preserve paragraph structure
        cleaned_text = clean_unicode_text(text)
        
        # Convert Markdown to HTML with extended features
        # DON'T collapse double newlines - they create paragraph breaks
        html_content = markdown2.markdown(cleaned_text, extras=[
            'fenced-code-blocks', 
            'tables', 
            'strike',
            'task_list',
            'spoiler',
            'footnotes',
            'header-ids'
        ])
        
        # Create beautiful PDF
        pdf_generator = BeautifulPDFGenerator(title, theme=theme)
        
        # Add title page if requested
        if include_title_page:
            pdf_generator.add_title_page()
            
        pdf_generator.write_html(html_content)
        pdf_generator.generate_pdf(pdf_path)
        
        # Upload to S3
        try:
            bucket_name = docs_bucket_name
            folder_name = 'uploads'
            file_key = f"{folder_name}/{title}.pdf"
            s3_client = boto3.client('s3')
            s3_client.upload_file(pdf_path, bucket_name, file_key)
            s3_status = "uploaded to S3"
        except NameError:
            s3_status = "S3 upload skipped (docs_bucket_name not defined)"
        except Exception as s3_error:
            s3_status = f"S3 upload failed: {s3_error}"
        
        # Upload to Slack
        try:
            send_file_to_slack(pdf_path, chat_id, title, ts)
            slack_status = "sent to Slack"
        except NameError:
            slack_status = "Slack upload skipped (send_file_to_slack not defined)"
        except Exception as slack_error:
            slack_status = f"Slack upload failed: {slack_error}"
        
        status = f"Success: Beautiful PDF generated with {theme} theme, {s3_status}, and {slack_status}."
        
    except Exception as e:
        status = f"Failure: {str(e)}"
        
    finally:
        # Clean up temporary file
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            
    return status


# Backward compatibility aliases
class MyFPDF:
    """Compatibility class - redirects to BeautifulPDFGenerator"""
    def __init__(self, title):
        print("Warning: MyFPDF is deprecated. Use BeautifulPDFGenerator instead.")
        self.generator = BeautifulPDFGenerator(title)
        
    def write_html(self, html):
        return self.generator.write_html(html)
        
    def output(self, path, dest='F'):
        return self.generator.generate_pdf(path)


def replace_problematic_chars(text):
    """Backward compatibility - redirects to clean_unicode_text"""
    return clean_unicode_text(text)


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
    

def ask_bighead(prompt, model_option='pro'):
    model_map = {
        'ultra': 'gemini-1.0-ultra-latest',
        'pro': 'gemini-1.5-pro-latest',
        'vision': 'gemini-pro-vision'
    }
    model = model_map.get(model_option.lower())
    if not model:
        raise ValueError(f'Invalid model option: {model_option}. Choose from "pro", or "vision".')

    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_api_key}'
    headers = {'Content-Type': 'application/json'}
    data = {
        'contents': [{
            'parts': [{
                'text': prompt
            }]
        }]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raises an HTTPError if the status is 4xx or 5xx   
        response_json = response.json()
        print(json.dumps(response_json))
        if 'candidates' in response_json and response_json['candidates']:
            first_candidate = response_json['candidates'][0]
            if 'content' in first_candidate and 'parts' in first_candidate['content'] and first_candidate['content']['parts']:
                response_text = first_candidate['content']['parts'][0]['text']
                #print(response_text)
                return to_markdown(response_text)
        return None
    except requests.exceptions.HTTPError as e:
        return f'HTTP error occurred: {e.response.text}'
    except requests.exceptions.RequestException as e:
        return f'Request error occurred: {e}'
    except Exception as e:
        return f'An error occurred: {e}'
        

def to_markdown(text):
    text = text.replace('•', '  *')
    indented_text = textwrap.indent(text, '> ', predicate=lambda _: True)
    html = markdown2.markdown(indented_text)
    return html
     
        
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

def is_serializable(value):
    """Helper function to check if a value is serializable."""
    try:
        json.dumps(value)
        return True
    except (TypeError, OverflowError):
        return False


def normalize_message(response):
    # If it's a dictionary (raw JSON format)
    if isinstance(response, dict):
        message = response['choices'][0]['message']
        return type('Message', (), {
            'content': message.get('content'),
            'audio': message.get('audio'),
            'tool_calls': message.get('tool_calls')
        })
    # If it's already an OpenAI object
    return response.choices[0].message
