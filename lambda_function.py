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
from fpdf import FPDF
from io import BytesIO, StringIO
from odoo_functions import authenticate, odoo_get_mapped_models, odoo_get_mapped_fields, odoo_create_record, odoo_fetch_records, odoo_update_record, odoo_delete_record
from openai import OpenAIError, BadRequestError
from prompts import prompts  # Import the prompts from prompts.py
from semantic_router import Route
from semantic_router import RouteLayer
from semantic_router.encoders import OpenAIEncoder
from tools import tools #Import tools from tools.py
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urlparse, unquote, quote_plus, urlencode, urljoin
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
from weaviate.classes.query import Sort
from xml.etree import ElementTree

from extservices import get_coordinates
from extservices import get_weather_data

from nltk.tokenize import sent_tokenize, word_tokenize
from config import *  # Import all configuration variables
from storage import (
    save_message_weaviate, get_last_messages_weaviate, 
    get_relevant_messages, save_message, get_last_messages,
    get_message_by_sort_id, get_messages_in_range, get_users, 
    get_channels, manage_mute_status, decimal_default
)

from slack_integration import (
    send_slack_message, send_audio_to_slack, send_file_to_slack,
    get_slack_user_name, update_slack_users, update_slack_conversations,
    find_image_urls, latex_to_slack, message_to_json
)

from media_processing import (
    text_to_speech, upload_image_to_s3, transcribe_speech_from_memory,
    download_audio_to_memory, process_url, transcribe_multiple_urls,
    convert_to_wav_in_memory
)

from conversation import (
    make_text_conversation, make_vision_conversation, make_audio_conversation,
    make_openai_vision_call, make_openai_audio_call, ask_openai_o1,
    serialize_chat_completion_message, handle_message_content, handle_tool_calls
)

from nlp_utils import (
    load_stopwords, rank_sentences, summarize_record, summarize_messages,
    clean_website_data, detect_pii
)

nltk.data.path.append("/opt/python/nltk_data")

# Any remaining global variables that need to stay in the main file
current_datetime = datetime.datetime.now(UTC)

# Connect to Weaviate Cloud
weaviate_client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
    headers = headers
)


def lambda_handler(event, context):
    print(f"Event: {event}")   
    
    global stopwords
    global chat_id
    global user_id
    global thread_ts
    global audio_text
    global conversation

    stopwords = load_stopwords('english')
    has_image = ''
    audio_text = ''
    has_audio = False
    image_urls = []   
    has_image_urls = False
    relevant = 5

    rl = RouteLayer.from_json("routes_layer.json")
    
    if 'Records' in event and isinstance(event['Records'], list):
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
    
        # Parse the incoming event from Slack          
        slack_event = json.loads(event['body'])
        event_type = slack_event['event']['type']
        #print(event_type)
          
        #Initialize global variables        
        chat_id = slack_event['event']['channel']
        #print(f"Chat Id: {chat_id}")
        
        thread_ts = slack_event['event'].get('thread_ts', slack_event['event']['ts'])
    
        # Check if the 'user' key exists and has a value 
        if 'user' in slack_event['event'] and slack_event['event']['user']:
            user_id = slack_event['event']['user']
        else:
            # Stop execution if no user ID is found 
            print("No user ID found. Stopping execution.")
            return {
               'statusCode': 200,
               'body': json.dumps({'message': 'Ignored message.'})
            } # or use 'exit()' or 'sys.exit()' depending on the context  
    
        
        # Ignore messages from the bot itself  
        if 'event' in slack_event and 'bot_id' in slack_event['event']:
               return {
                   'statusCode': 200,
                   'body': json.dumps({'message': 'Ignored message from bot'})
               }
        
        # Retrieve the name of the user         
        user = get_users(user_id)
        user_name = user['real_name']
        display_name = user['display_name']
        display_name = display_name.replace(' ', '_').replace('.', '').strip()
        
        try:
            text = slack_event['event']['text']
        except KeyError:
            print(f"An error occured. No text found. slack_event: {json.dumps(slack_event)}") # Handle the error, e.g., log it and set a default value for text
            text = ""
        
        #Check for image in message 
        try:
            for file in slack_event["event"]["files"]:
                if file["mimetype"].startswith("image/"):
                    image_url = file["url_private"]
                    uploaded_url = upload_image_to_s3(image_url, image_bucket_name)
                    image_urls.append(uploaded_url)
                    
            #print(json.dumps(image_urls))
        except KeyError:
            image_urls = None    
    

        audio_urls = []
        speech_instruction = prompts['speech_instruction']


        try:
            route_name = ""
            if text:
                # Try to get the route choice
                try:
                    route_choice = rl(text)
                    print(f'Route Choice: {route_choice}')
                    route_name = route_choice.name
                except ValueError as e:
                    # Handle the specific error for context length exceeded
                    if "maximum context length" in str(e):
                        print(f"Warning: Text exceeds maximum context length. Using fallback routing. Error: {e}")
                        # Implement a fallback strategy - options:
                        # 1. Truncate the text to fit within limits
                        # 2. Use a default route
                        # 3. Split the text and process in chunks
                        
                        # Example of fallback to default route:
                        route_name = "default_route"  # Replace with your fallback route
                    else:
                        # Re-raise if it's a different ValueError
                        raise
        except Exception as e:
            # Catch any other exceptions that might occur
            print(f"Error in routing: {e}")
            # Set a default route or handle the error appropriately
            route_name = "unknown_route"  # Replace with appropriate error handling

        # Check for audio in message     
        try:
            for file in slack_event["event"]["files"]:
                if file["mimetype"].startswith(("audio/", "video/")):
                    audio_url = file["url_private"]
                    audio_urls.append(audio_url)

            print(json.dumps(audio_urls))
            
            audio_text = transcribe_multiple_urls(audio_urls)
            #Check if audio_text is not empty  
            if audio_text:
                # Append speech_instruction to audio_text where audio_text is a list and speech_instruction is a string
                audio_text.append(speech_instruction)
                # Convert the array to a string with spaces in between each element
                combined_text = ' '.join(audio_text)
            print(f"Audio Msgs: {audio_text}")
            #has_audio = len(audio_urls) > 0
            
        except KeyError:
            audio_urls = None
       
        size_limit_mb = 5  # Set the file size limit in MB
    
        # Check for documents in message
        try:
            application_files = []
            for file in slack_event["event"]["files"]:
                if file["mimetype"].startswith("application/") or file["mimetype"].startswith("text/"):
                    file_url = file["url_private"]
                    file_name = file.get("name", "Unnamed File")
                    #print(f"Mime Type: {file['mimetype']}")
                    file_size_mb = file.get("size", 1) / (1024 * 1024)
                    if file_size_mb > size_limit_mb:
                        application_files.append({"file_name": file_name, "content": f"File {file_name} is over the {size_limit_mb} MB limit. URL: {file_url}"})
                    else:
                        file_content = download_and_read_file(file_url, file["mimetype"])
                        application_files.append({"Message": "The user sent a file with this message. The contents of the file have been appended to this message.", "Filename": file_name, "content": file_content})
        
            print(json.dumps(application_files))   
        except KeyError:
            application_files = None
    
        # Check if there are attachments in the incoming message       
        if 'attachments' in slack_event['event']:
            attachments = slack_event['event']['attachments']
            
            # Extract content from attachments and append it to the text       
            for attachment in attachments:
                if 'text' in attachment:
                    forwarded_message_text = attachment['text']
                    # Append the forwarded message text along with a notice. 
                    text += f"\n\nForwarded Message:\n{forwarded_message_text}"
                    
        text += " " + " ".join(audio_text) if audio_text else ""
        text += " " + json.dumps(application_files) if application_files else ""

        # Retrieve the last N messages from the user and assistant     
        if route_name == 'chitchat':
            summary_len = 0
            full_text_len = 2
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

        # Extract and combine message history 
        user_msg_history, user_messages = (lambda x: (x[full_text_len:], x[:full_text_len]))(get_last_messages_weaviate(user_table, chat_id, num_messages))
        #print(json.dumps(user_messages, default=decimal_default))
    
        asst_msg_history, assistant_messages = (lambda x: (x[full_text_len:], x[:full_text_len]))(get_last_messages_weaviate(assistant_table, chat_id, num_messages))
        #print(json.dumps(asst_msg_history, default=decimal_default))   
    
        msg_history = user_msg_history + asst_msg_history
        msg_history.sort(key=lambda x: x['sort_key'])
        #print(json.dumps(msg_history, default=decimal_default))  
        
        msg_history_summary = [summarize_messages(msg_history)]
        #print(f"Message History Summary: {json.dumps(msg_history_summary, default=decimal_default)}")    

        if relevant > 0:
            # Set to empty lists rather than None when text is empty
            relevant_user_messages = get_relevant_messages(user_table, chat_id, text, relevant) if text else []
            relevant_assistant_messages = get_relevant_messages(assistant_table, chat_id, text, relevant) if text else []
        else:
            relevant_user_messages = []
            relevant_assistant_messages = []

        # Combine and sort relevant messages from user and assistant by sort_key
        all_relevant_messages = relevant_user_messages + relevant_assistant_messages
        all_relevant_messages.sort(key=lambda x: x['sort_key'])
        
        # Combine and sort messages from user and assistant by sort_key
        all_messages = user_messages + assistant_messages
        all_messages.sort(key=lambda x: x['sort_key'])
        #print(json.dumps(all_messages, default=decimal_default))  
        
        try:
            maria_muted = manage_mute_status(chat_id)[0]
            match_id = re.search(r"<@(\w+)>", slack_event['event']['text'])
            mentioned_user_id = match_id.group(1) if match_id else None
            print(f"Maria muted: {maria_muted}")
            # Check if Maria is muted and the mentioned user is not the specified ID
            if maria_muted and mentioned_user_id != "U05SSQR07RS":
                print("We are in the Maria is muted IF...")
                save_message(meetings_table, chat_id, text, "user", thread_ts, image_urls)
                return  # Exit the function after saving the message
        except Exception as e:
            print(f"An unexpected error occurred: {e}")            
        
        # Check if image_urls exists
        has_image_urls, all_image_urls = find_image_urls(all_messages)

        if enable_pii:
            text = detect_pii(text)

        if has_audio:
            # Use audio conversation for audio inputs
            conversation = make_audio_conversation(system_text, assistant_text, display_name, 
                                                all_relevant_messages, msg_history_summary, 
                                                all_messages, text, audio_urls)
            # Use the audio-specific model
            response_message = make_openai_audio_call(client, conversation)
        elif image_urls or has_image_urls:
            # Keep the existing vision conversation path for images
            conversation = make_vision_conversation(system_text, assistant_text, display_name, 
                                                all_relevant_messages, msg_history_summary, 
                                                all_messages, text, image_urls)
            response_message = make_openai_vision_call(client, conversation)
        else:
            # Regular vision conversation for text-only
            conversation = make_vision_conversation(system_text, assistant_text, display_name, 
                                                all_relevant_messages, msg_history_summary, 
                                                all_messages, text)
            response_message = make_openai_vision_call(client, conversation)

    # Save the user's message to Database 
    save_message_weaviate(user_table, chat_id, text, thread_ts, image_urls)

    # Define available functions    
    available_functions = {
        "browse_internet": browse_internet,
        "google_search": google_search,
        "get_coordinates": get_coordinates,
        "get_weather_data": get_weather_data,
        "get_message_by_sort_id": get_message_by_sort_id,
        "get_messages_in_range": get_messages_in_range,
        "send_slack_message": send_slack_message,
        "send_audio_to_slack": send_audio_to_slack,
        "send_file_to_slack": send_file_to_slack,        
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
        "ask_openai_o1": ask_openai_o1,
        "get_embedding": get_embedding,
        "manage_mute_status": manage_mute_status,
        "search_and_format_products": search_and_format_products
    }    

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
            handle_message_content(response_message, event_type, thread_ts, chat_id, audio_text)

        # Check and process tool calls
        if has_tool_calls:
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
                # Default to vision API
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
    web_pages = asyncio.run(get_web_pages(urls, full_text))
    print(web_pages)
    return web_pages


async def get_web_pages(urls, full_text=False, max_concurrent_requests=5):
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(max_concurrent_requests)
        tasks = [process_page(session, url, semaphore, full_text) for url in urls]
        results = await asyncio.gather(*tasks)
        
        # Flatten the list of results
        flattened_results = [item for sublist in results for item in sublist]
        print(json.dumps(flattened_results))
        
        return flattened_results


async def fetch_page(session, url, timeout=30):
    headers = {
        'User-Agent': random.choice(USER_AGENTS)
    }    
    try:
        async with session.get(url, headers=headers, proxy=proxy_url, timeout=timeout) as response:
            #print(f"Search Result: {response}")
            content_type = response.headers.get('Content-Type', '')
            if 'text' in content_type:
                encoding = response.charset or 'utf-8'
                return await response.text(encoding=encoding)
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

async def process_page(session, url, semaphore, full_text=False):
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
                    summary_or_full_text = rank_sentences(cleaned_text, stopwords, max_sentences=150)  # Placeholder for the rank_sentences function
                else:
                    try:
                        summary_or_full_text = rank_sentences(cleaned_text, stopwords, max_sentences=50)  # Placeholder for the rank_sentences function
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
                            #logging.warning(f"Skipping data URI image: {img_url[:30]}...")  # Log a warning and skip data URIs
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
    

def download_and_read_file(url, content_type):
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
            #print(f"File Name: {tmp_file.name}")
            
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
                summary = rank_sentences(text, stopwords, max_sentences=50)
                return summary
            elif 'text/plain' in content_type:
                with open(tmp_file.name, 'r') as f:
                    content = f.read()
                return content
            else:
                return 'Unsupported file type'
    except requests.exceptions.RequestException as e:
        return f'Error downloading file: {e}'
    except Exception as e:
        return f'Error processing file: {e}'
        

class MyFPDF(FPDF):
    def __init__(self, title):
        super().__init__()
        self.title = title
        self.inside_list = False

    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, self.title, 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def write_html(self, html):
        # Simple HTML parsing (extend this for more tags)
        html = html.replace('<strong>', '<b>').replace('</strong>', '</b>')
        html = html.replace('<em>', '<i>').replace('</em>', '</i>')

        # Split the HTML into parts
        parts = re.split(r'(</?[^>]+>)', html)
        for part in parts:
            # Detect and handle opening tags
            if part.startswith('<b>'):
                self.set_font('Arial', 'B', 11)
                continue
            if part.startswith('<i>'):
                self.set_font('Arial', 'I', 11)
                continue
            if part.startswith('<h1>'):
                self.set_font('Arial', 'B', 16)
                continue
            if part.startswith('<h2>'):
                self.set_font('Arial', 'B', 14)
                continue
            if part.startswith('<h3>'):
                self.set_font('Arial', 'B', 12)
                continue
            if part.startswith('<p>'):
                self.set_font('Arial', '', 11)
                continue
            if part.startswith('<ul>'):
                self.inside_list = True
                continue
            if part.startswith('<li>'):
                self.set_font('Arial', '', 11)
                part = '• ' + part[4:]
            
            # Detect and handle closing tags
            if part.startswith('</'):
                self.set_font('Arial', '', 11)
                if part.startswith('</h1>') or part.startswith('</h2>') or part.startswith('</h3>'):
                    self.ln(10)  # Add a line break after headers
                if part.startswith('</ul>'):
                    self.inside_list = False
                if part.startswith('</li>') and self.inside_list:
                    self.ln(5)  # Add a line break after list items
                continue

            # Write the actual text content   
            self.multi_cell(0, 8, part)


def replace_problematic_chars(text):
    # Replace common problematic Unicode characters with ASCII equivalents
    replacements = {
        '\u2018': "'",  # Left single quotation mark
        '\u2019': "'",  # Right single quotation mark
        '\u201c': '"',  # Left double quotation mark
        '\u201d': '"',  # Right double quotation mark
        '\u2013': '-',  # En dash
        '\u2014': '-',  # Em dash
        '\u2026': '...',  # Ellipsis
        '\u2022': '*',  # Bullet point
        '\u00A0': ' ',  # Non-breaking space
        '\u2010': '-',  # Hyphen
        '\u2012': '-',  # Figure dash
        '\u2015': '-',  # Horizontal bar
    }
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)
    return text


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
