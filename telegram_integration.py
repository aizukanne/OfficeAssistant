from config import telegram_bot_token

from storage import (
    get_users, get_channels
)


def process_telegram_event(telegram_event):
    """Process Telegram event and return standardized parameters"""
    try:
        message = telegram_event['message']
        event_type = 'message'  # Telegram equivalent
        
        # Extract chatId and text from the incoming message
        chat_id = str(message['chat']['id'])  # Convert to string for consistency with Slack
        
        if 'text' in message:
            text = str(message['text'])
        else:
            text = "Smiley"  # or some default value
        
        # Extract the sender's first_name, clean it up and use it as user name
        user_name = message['from'].get('first_name', '')
        # If first_name starts with '@', remove it
        if user_name.startswith('@'):
            user_name = user_name[1:]
        # Remove any non-alphabetical characters
        user_name = re.sub(r'[^a-zA-Z]', '', user_name)
        # If name is null or empty, replace with "Stranger!" 
        if not user_name:
            user_name = "Stranger!"
        
        # For Telegram, we'll use user_name as display_name and user_id
        user_id = str(message['from']['id'])
        display_name = user_name
        
        # Generate thread_ts equivalent (Telegram doesn't have threads, so use message timestamp)
        thread_ts = str(message.get('date', time.time()))
        
        # Initialize empty lists for features not yet implemented in Telegram
        image_urls = []
        audio_urls = []
        audio_text = []
        application_files = []
        
        # TODO: Implement image, audio, and document processing for Telegram
        # This would involve checking message['photo'], message['audio'], message['document'], etc.
        # For now, we'll leave these empty but the structure is ready for future implementation
        
        return {
            'chat_id': chat_id,
            'user_id': user_id,
            'user_name': user_name,
            'display_name': display_name,
            'text': text,
            'thread_ts': thread_ts,
            'image_urls': image_urls,
            'audio_urls': audio_urls,
            'audio_text': audio_text,
            'application_files': application_files,
            'event_type': event_type
        }
        
    except Exception as e:
        print(f"Error processing Telegram event: {e}")
        return None


def send_telegram_message(chat_id, message):
    # Telegram Bot URL
    url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"

    # Message data
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }

    # Send POST request to Telegram Bot API
    response = requests.post(url, data=data)

    return response.json()