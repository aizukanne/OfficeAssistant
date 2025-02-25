import json
import logging
from typing import Dict, Any, Optional

from ..core.config import (
    USER_TABLE,
    ASSISTANT_TABLE,
    MEETINGS_TABLE
)
from ..core.middleware import lambda_middleware
from ..core.error_handlers import APIError, handle_errors

from ..clients.openai_client import make_openai_call
from ..clients.slack_client import send_slack_message, send_audio_to_slack

from ..services.conversation_builder import (
    make_text_conversation,
    make_vision_conversation,
    make_audio_conversation
)
from ..services.message_processing import load_stopwords
from ..services.web_services import google_search, browse_internet

from ..data.db_operations import save_message, get_last_messages
from ..data.user_management import get_users
from ..data.channel_management import manage_mute_status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@lambda_middleware
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda function handler.
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        API Gateway response object
    """
    logger.info(f"Event: {event}")
    
    try:
        # Initialize global variables
        global stopwords, chat_id, user_id, thread_ts, audio_text, conversation
        
        stopwords = load_stopwords('english')
        has_image = ''
        audio_text = ''
        image_urls = []
        has_image_urls = False
        
        # Handle email records
        if 'Records' in event and isinstance(event['Records'], list):
            return handle_email_event(event)
            
        # Handle Slack events
        return handle_slack_event(event)
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }

def handle_email_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle incoming email events.
    
    Args:
        event: Lambda event object
        
    Returns:
        API Gateway response object
    """
    try:
        payload = event['Records'][0]['body']
        body_str = json.loads(payload)['payload']['event']
        event_type = body_str['type']
        
        system_text = prompts['system_text']  # This needs to be imported
        email_instructions = prompts['email_instructions']  # This needs to be imported
        
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
        text = f"Email: {body_str}"
        conversation = make_vision_conversation(
            system_text,
            email_instructions,
            display_name,
            '',
            '',
            text
        )
        response_message = make_openai_call(client, conversation)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Email processed successfully'})
        }
        
    except Exception as e:
        logger.error(f"Error handling email event: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to process email',
                'details': str(e)
            })
        }

def handle_slack_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle incoming Slack events.
    
    Args:
        event: Lambda event object
        
    Returns:
        API Gateway response object
    """
    try:
        # Parse Slack event
        slack_event = json.loads(event['body'])
        event_type = slack_event['event']['type']
        
        # Initialize variables
        global chat_id, thread_ts, user_id
        chat_id = slack_event['event']['channel']
        thread_ts = slack_event['event'].get('thread_ts', slack_event['event']['ts'])
        
        # Validate user ID
        if 'user' not in slack_event['event'] or not slack_event['event']['user']:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Ignored message.'})
            }
        
        user_id = slack_event['event']['user']
        
        # Ignore bot messages
        if 'bot_id' in slack_event['event']:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Ignored message from bot'})
            }
        
        # Get user information
        user = get_users(user_id)
        user_name = user['real_name']
        display_name = user['display_name'].replace(' ', '_').replace('.', '').strip()
        
        # Get message text
        text = slack_event['event'].get('text', '')
        
        # Process message
        return process_message(
            text,
            event_type,
            display_name,
            slack_event
        )
        
    except Exception as e:
        logger.error(f"Error handling Slack event: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to process Slack event',
                'details': str(e)
            })
        }

def process_message(
    text: str,
    event_type: str,
    display_name: str,
    slack_event: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process incoming message and generate response.
    
    Args:
        text: Message text
        event_type: Type of event
        display_name: User's display name
        slack_event: Full Slack event object
        
    Returns:
        API Gateway response object
    """
    try:
        # Check if Maria is muted
        maria_muted = manage_mute_status()[0]
        match_id = re.search(r"<@(\w+)>", text)
        mentioned_user_id = match_id.group(1) if match_id else None
        
        if maria_muted and mentioned_user_id != "U05SSQR07RS":
            save_message(MEETINGS_TABLE, chat_id, text, "user", thread_ts, image_urls)
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Message saved (Maria is muted)'})
            }
        
        # Process attachments
        if 'attachments' in slack_event['event']:
            for attachment in slack_event['event']['attachments']:
                if 'text' in attachment:
                    text += f"\n\nForwarded Message:\n{attachment['text']}"
        
        # Add audio text if present
        if audio_text:
            text += f" {' '.join(audio_text)}"
        
        # Save user message
        save_message(USER_TABLE, chat_id, text, "user", thread_ts, image_urls)
        
        # Generate and process response
        response_message = generate_response(text, display_name)
        
        # Handle response
        if response_message:
            handle_response(response_message, event_type)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Message processed successfully'})
        }
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to process message',
                'details': str(e)
            })
        }

def generate_response(text: str, display_name: str) -> Optional[Dict[str, Any]]:
    """
    Generate response using OpenAI API.
    
    Args:
        text: Input text
        display_name: User's display name
        
    Returns:
        OpenAI API response
    """
    try:
        # Get message history
        user_messages = get_last_messages(USER_TABLE, chat_id, 10)
        assistant_messages = get_last_messages(ASSISTANT_TABLE, chat_id, 10)
        
        # Combine and sort messages
        all_messages = user_messages + assistant_messages
        all_messages.sort(key=lambda x: x['sort_key'])
        
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
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}", exc_info=True)
        return None

def handle_response(
    response_message: Dict[str, Any],
    event_type: str
) -> None:
    """
    Handle API response and send to appropriate channel.
    
    Args:
        response_message: API response message
        event_type: Type of event
    """
    try:
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
        save_message(
            ASSISTANT_TABLE,
            chat_id,
            assistant_reply,
            "assistant",
            thread_ts
        )
        
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
                
    except Exception as e:
        logger.error(f"Error handling response: {str(e)}", exc_info=True)