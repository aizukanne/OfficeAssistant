import json
import time
import logging
import re
from typing import Dict, Any, Optional
import concurrent.futures
from decimal import Decimal

from semantic_router import Route, RouteLayer
from semantic_router.encoders import OpenAIEncoder

from ..core.config import (
    USER_TABLE,
    ASSISTANT_TABLE,
    MEETINGS_TABLE,
    IMAGE_BUCKET_NAME
)

from extservices import get_coordinates, get_weather_data
from ..core.error_handlers import APIError

from ..clients.openai_client import client, make_openai_call
from ..clients.slack_client import send_slack_message, send_audio_to_slack, send_file_to_slack

from ..services.conversation_builder import (
    make_text_conversation,
    make_vision_conversation,
    make_audio_conversation
)
from ..services.message_processing import (
    load_stopwords,
    summarize_messages
)
from ..services.web_services import google_search, browse_internet
from ..services.audio_processing import transcribe_multiple_urls
from ..utils.file_operations import upload_image_to_s3

from ..data.db_operations import save_message, get_last_messages
from ..data.user_management import get_users
from ..data.channel_management import manage_mute_status

from prompts import prompts  # Import the prompts from prompts.py

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
stopwords = None
chat_id = None
user_id = None
thread_ts = None
audio_text = None
conversation = None
image_urls = []
system_text = prompts['system_text']
assistant_text = prompts['assistant_text']

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
    "get_embedding": get_embedding,
    "manage_mute_status": manage_mute_status
}

def lambda_handler(event, context):
    """
    Main Lambda function handler.
    
    Args:
        event: Lambda event object
        context: Lambda context object
    """
    logger.info(f"Event: {event}")
    
    try:
        # Initialize global variables
        global stopwords, chat_id, user_id, thread_ts, audio_text, conversation, image_urls
        
        stopwords = load_stopwords('english')
        has_image = ''
        audio_text = ''
        image_urls = []
        has_image_urls = False
        
        rl = RouteLayer.from_json("routes_layer.json")
        
        if 'Records' in event and isinstance(event['Records'], list):
            handle_email_event(event)
        else:
            handle_slack_event(event)
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}", exc_info=True)

def handle_email_event(event):
    """Handle incoming email events."""
    payload = event['Records'][0]['body']
    body_str = json.loads(payload)['payload']['event']
    event_type = body_str['type']
    
    system_text = prompts['system_text']
    email_instructions = prompts['email_instructions']
    
    # Get thread timestamp
    timestamp = time.time()
    thread_ts = f"{timestamp:.6f}"
    
    chat_id = "C06QL84KZGQ"
    user_id = "U02RPR2RMJS"
    
    # Get user information
    user = get_users(user_id)
    user_name = user['real_name']
    display_name = user['display_name'].replace(' ', '_').replace('.', '').strip()
    
    # Process email
    text = f"Email: {body_str} "
    conversation = make_vision_conversation(
        system_text,
        email_instructions,
        display_name,
        '',
        '',
        text
    )
    response_message = make_openai_call(client, conversation)

def handle_slack_event(event):
    """Handle incoming Slack events."""
    body_str = event.get('body', '{}')
    logger.info(f"Body: {body_str}")

    # Parse Slack event
    slack_event = json.loads(event['body'])
    event_type = slack_event['event']['type']
    
    # Initialize global variables
    global chat_id, thread_ts, user_id
    chat_id = slack_event['event']['channel']
    thread_ts = slack_event['event'].get('thread_ts', slack_event['event']['ts'])

    # Check if the 'user' key exists and has a value
    if 'user' not in slack_event['event'] or not slack_event['event']['user']:
        logger.info("No user ID found. Stopping execution.")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Ignored message.'})
        }

    user_id = slack_event['event']['user']
    
    # Ignore messages from the bot itself
    if 'event' in slack_event and 'bot_id' in slack_event['event']:
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Ignored message from bot'})
        }

    # Process message
    process_message(slack_event, event_type)

def process_message(slack_event, event_type):
    """Process incoming Slack message."""
    # Get user information
    user = get_users(user_id)
    user_name = user['real_name']
    display_name = user['display_name'].replace(' ', '_').replace('.', '').strip()
    
    # Get message text
    try:
        text = slack_event['event']['text']
    except KeyError:
        logger.error(f"No text found. slack_event: {json.dumps(slack_event)}")
        text = ""

    # Process attachments and files
    text = process_attachments(slack_event, text)
    
    # Check mute status
    try:
        maria_muted = manage_mute_status(chat_id)[0]
        match_id = re.search(r"<@(\w+)>", slack_event['event']['text'])
        mentioned_user_id = match_id.group(1) if match_id else None
        
        if maria_muted and mentioned_user_id != "U05SSQR07RS":
            logger.info("Maria is muted")
            save_message(MEETINGS_TABLE, chat_id, text, "user", thread_ts, image_urls)
            return
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

    # Save user message
    save_message(USER_TABLE, chat_id, text, "user", thread_ts, image_urls)

    # Generate initial response
    response_message = generate_response(text, display_name)
    while response_message:
        # Handle content/audio if present
        if isinstance(response_message, dict):
            has_content = response_message.get("content")
            has_audio = response_message.get("audio")
            has_tool_calls = response_message.get("tool_calls")
        else:
            has_content = getattr(response_message, "content", None)
            has_audio = getattr(response_message, "audio", None)
            has_tool_calls = getattr(response_message, "tool_calls", None)

        if has_content or has_audio:
            handle_response(response_message, event_type)
        
        # Check for tool calls
        if has_tool_calls:
            conversation_with_tool_responses = handle_tool_calls(
                response_message, available_functions, chat_id, conversation, thread_ts
            )
            # Make follow-up API call
            if image_urls:
                response_message = make_openai_call(client, conversation_with_tool_responses)
            else:
                response_message = make_openai_call(client, conversation_with_tool_responses)
        else:
            break

def process_attachments(slack_event, text):
    """Process attachments and files in Slack message."""
    global image_urls, audio_text

    # Process images
    try:
        for file in slack_event["event"]["files"]:
            if file["mimetype"].startswith("image/"):
                image_url = file["url_private"]
                uploaded_url = upload_image_to_s3(image_url, IMAGE_BUCKET_NAME)
                image_urls.append(uploaded_url)
    except KeyError:
        pass

    # Process audio
    try:
        audio_urls = []
        for file in slack_event["event"]["files"]:
            if file["mimetype"].startswith(("audio/", "video/")):
                audio_url = file["url_private"]
                audio_urls.append(audio_url)
        
        if audio_urls:
            audio_text = transcribe_multiple_urls(audio_urls)
            if audio_text:
                text += f" {' '.join(audio_text)}"
    except KeyError:
        pass

    # Process attachments
    if 'attachments' in slack_event['event']:
        for attachment in slack_event['event']['attachments']:
            if 'text' in attachment:
                text += f"\n\nForwarded Message:\n{attachment['text']}"

    return text

def generate_response(text: str, display_name: str) -> Optional[Dict[str, Any]]:
    """Generate response using OpenAI API."""
    # Get message history
    user_messages = get_last_messages(USER_TABLE, chat_id, 10)
    assistant_messages = get_last_messages(ASSISTANT_TABLE, chat_id, 10)
    
    # Combine and sort messages
    all_messages = user_messages + assistant_messages
    all_messages.sort(key=lambda x: x['sort_key'])
    
    # Get message history summary
    msg_history = all_messages[2:]  # Skip the last 2 messages
    msg_history_summary = summarize_messages(msg_history, stopwords)
    
    # Create conversation
    if image_urls:
        conversation = make_vision_conversation(
            system_text,
            assistant_text,
            display_name,
            msg_history_summary,
            all_messages,
            text,
            image_urls
        )
    else:
        conversation = make_text_conversation(
            system_text,
            assistant_text,
            display_name,
            msg_history_summary,
            all_messages,
            text
        )
    
    # Get response from OpenAI
    return make_openai_call(client, conversation)

def handle_response(response_message: Dict[str, Any], event_type: str) -> None:
    """Handle API response and send to appropriate channel."""
    global audio_text

    # Extract message content
    if isinstance(response_message, dict):
        if "audio" in response_message:
            assistant_reply = response_message["audio"].get("transcript", "")
            audio_text = assistant_reply
        else:
            assistant_reply = response_message["content"]
    else:
        if getattr(response_message, "audio", None):
            assistant_reply = response_message.audio.get("transcript", "")
            audio_text = assistant_reply
        else:
            assistant_reply = response_message.content

    # Save assistant message
    save_message(ASSISTANT_TABLE, chat_id, assistant_reply, "assistant", thread_ts)

    # Send response
    if event_type in ['app_mention', 'New Email']:
        if audio_text:
            send_audio_to_slack(assistant_reply, chat_id, thread_ts)
        else:
            send_slack_message(assistant_reply, chat_id, thread_ts)
    else:
        if audio_text:
            send_audio_to_slack(assistant_reply, chat_id, None)
        else:
            send_slack_message(assistant_reply, chat_id, None)

def serialize_chat_completion_message(message):
    """
    Converts a ChatCompletionMessage object into a serializable dictionary.
    """
    message_dict = {
        "content": message.content,
        "role": message.role
    }

    # Serialize the function_call if it exists
    if message.function_call:
        message_dict["function_call"] = {
            "name": message.function_call.name,
            "arguments": message.function_call.arguments
        }

    # Serialize tool_calls if they exist
    if message.tool_calls:
        message_dict["tool_calls"] = []
        for tool_call in message.tool_calls:
            message_dict["tool_calls"].append({
                "id": tool_call.id,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments
                },
                "type": tool_call.type
            })

    return message_dict

def handle_tool_calls(response_message, available_functions, chat_id, conversations, thread_ts):
    tool_calls = response_message.tool_calls

    response_message_dict = serialize_chat_completion_message(response_message)
    conversations.append(response_message_dict)
    
    def process_tool_call(tool_call):
        try:
            function_name = tool_call.function.name
            function_to_call = available_functions.get(function_name)

            if function_to_call:
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)

                if not isinstance(function_response, str):
                    function_response = json.dumps(function_response, default=decimal_default)
                    print(f"Function Response: {function_response}")
                    if function_name != "google_search":
                        save_message(ASSISTANT_TABLE, chat_id, function_response, "assistant", thread_ts)
                    
                return {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
        except Exception as e:
            logging.error(f"Error processing tool call {tool_call.id}: {str(e)}")
            return {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": json.dumps({"error": str(e)}),
            }
        return None

    # Use ThreadPoolExecutor to process tool calls in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_tool_call = {executor.submit(process_tool_call, tool_call): tool_call for tool_call in tool_calls}
        
        for future in concurrent.futures.as_completed(future_to_tool_call):
            tool_call_result = future.result()
            if tool_call_result:
                conversations.append(tool_call_result)

    return conversations

def decimal_default(obj):
    """Helper function for JSON serialization of Decimal types."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")