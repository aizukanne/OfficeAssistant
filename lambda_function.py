import json
import nltk
from typing import Dict, Any, Optional

from src.config import (
    prompts,
    NLTK_DATA_PATH,
    DEFAULT_CHANNELS,
    get_dynamodb_table
)
from src.handlers import (
    make_vision_conversation,
    handle_message_content,
    handle_tool_calls
)
from src.services import (
    get_users,
    save_message,
    get_last_messages,
    upload_image_to_s3,
    make_openai_vision_call,
    manage_mute_status,
    # External Services
    get_coordinates,
    get_weather_data,
    get_message_by_sort_id,
    get_messages_in_range,
    # Slack Services
    send_slack_message,
    send_audio_to_slack,
    send_file_to_slack,
    get_channels,
    send_as_pdf,
    # OpenAI Services
    ask_openai_o1,
    get_embedding
)
from src.utils import (
    load_stopwords,
    tools
)
from src.services import (
    list_files,
    browse_internet,
    google_search
)

# Initialize NLTK data path
nltk.data.path = [NLTK_DATA_PATH]  # Override default paths to use only our configured path

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler function for processing incoming events.
    
    Args:
        event: The event data from AWS Lambda
        context: The runtime information from AWS Lambda
        
    Returns:
        Dict[str, Any]: Response containing status code and message
    """
    print(f"Event: {event}")

    # Initialize global variables
    global stopwords, chat_id, user_id, thread_ts, audio_text, conversation
    stopwords = load_stopwords('english')
    audio_text = ''
    image_urls = []
    has_image_urls = False

    # Load route layer configuration
    rl = RouteLayer.from_json("routes_layer.json")

    # Handle email records
    if 'Records' in event and isinstance(event['Records'], list):
        return handle_email_event(event, rl)

    # Handle Slack events
    return handle_slack_event(event, rl)

def handle_email_event(event: Dict[str, Any], rl: Any) -> Dict[str, Any]:
    """
    Handle incoming email events.
    
    Args:
        event: The email event data
        rl: Route layer instance
        
    Returns:
        Dict[str, Any]: Response containing status code and message
    """
    payload = event['Records'][0]['body']
    body_str = json.loads(payload)['payload']['event']
    event_type = body_str['type']

    # Set up email handling parameters
    thread_ts = f"{time.time():.6f}"
    chat_id = DEFAULT_CHANNELS['email_notifications']
    user_id = DEFAULT_CHANNELS['default_user']

    # Get user information
    user = get_users(user_id)
    display_name = user['display_name'].replace(' ', '_').replace('.', '').strip()
    
    # Prepare message
    text = f"Email: {body_str} "
    
    # Create conversation and get response
    conversation = make_vision_conversation(
        prompts['system_text'],
        prompts['email_instructions'],
        display_name,
        '',
        '',
        text
    )
    response_message = make_openai_vision_call(conversation)

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Email processed successfully'})
    }

def handle_slack_event(event: Dict[str, Any], rl: Any) -> Dict[str, Any]:
    """
    Handle incoming Slack events.
    
    Args:
        event: The Slack event data
        rl: Route layer instance
        
    Returns:
        Dict[str, Any]: Response containing status code and message
    """
    body_str = event.get('body', '{}')
    slack_event = json.loads(body_str)
    event_type = slack_event['event']['type']

    # Extract basic information
    chat_id = slack_event['event']['channel']
    thread_ts = slack_event['event'].get('thread_ts', slack_event['event']['ts'])
    
    # Validate user
    if not validate_user(slack_event):
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Ignored message.'})
        }

    # Get user information
    user = get_users(user_id)
    display_name = user['display_name'].replace(' ', '_').replace('.', '').strip()

    # Process message content
    text, image_urls, audio_urls, application_files = process_message_content(slack_event)
    
    # Handle routing
    route_name = get_route_name(text, rl) if text else ""
    system_text, assistant_text, summary_len, full_text_len = get_route_config(route_name)

    # Process message history
    msg_history_summary, all_messages = process_message_history(
        chat_id,
        summary_len,
        full_text_len
    )

    # Handle mute status
    if check_mute_status(slack_event):
        save_message(
            get_dynamodb_table('meetings'),
            chat_id,
            text,
            "user",
            thread_ts,
            image_urls
        )
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Message saved while muted'})
        }

    # Generate response
    response_message = generate_response(
        system_text,
        assistant_text,
        display_name,
        msg_history_summary,
        all_messages,
        text,
        image_urls
    )

    # Save user message
    save_message(
        get_dynamodb_table('user'),
        chat_id,
        text,
        "user",
        thread_ts,
        image_urls
    )

    # Process response
    process_response(response_message, event_type, thread_ts, chat_id)

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Success'})
    }

# Available functions for tool calls
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
    "ask_openai_o1": ask_openai_o1,
    "get_embedding": get_embedding,
    "manage_mute_status": manage_mute_status
}
