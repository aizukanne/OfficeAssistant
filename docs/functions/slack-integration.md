# Slack Integration

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [← Conversation Management](conversation-management.md) | [Storage Operations →](storage-operations.md)

The Slack integration module in `slack_integration.py` provides functionality for interacting with the Slack API, enabling Maria to send messages, upload files, and process Slack events.

## Overview

The Slack integration module handles:

- Sending messages to users and channels
- Uploading files and media to Slack
- Retrieving user and channel information
- Processing Slack events

## Message Operations

### Send Slack Message

```python
def send_slack_message(message, channel, ts=None)
```

This function sends a message to a Slack channel or user:

**Parameters:**
- `message`: The message text to send
- `channel`: The channel or user ID to send the message to
- `ts`: (Optional) Thread timestamp if replying to a thread

**Example:**
```python
# Send a message to a channel
send_slack_message("Hello everyone!", "C12345")

# Reply to a thread
send_slack_message("Here's the information you requested.", "C12345", "1609459200.000700")
```

**Example Usage:**

```
User: Can you send a reminder to the team?
Maria: I'll send a reminder to the team channel.
[Sends message to team channel]
I've sent the reminder to the team channel.
```

### Send Audio to Slack

```python
def send_audio_to_slack(text, chat_id=None, ts=None)
```

This function converts text to audio and sends it to Slack:

**Parameters:**
- `text`: The text to convert to audio
- `chat_id`: The channel or user ID to send the audio to
- `ts`: (Optional) Thread timestamp if replying to a thread

**Example:**
```python
send_audio_to_slack("Here's your audio message", "C12345")
```

**Example Usage:**

```
User: Can you send this as an audio message?
Maria: I'll convert that to audio and send it.
[Sends audio file to channel]
I've sent the audio message.
```

### Send File to Slack

```python
def send_file_to_slack(file_path, chat_id, title, ts=None)
```

This function uploads a file to Slack:

**Parameters:**
- `file_path`: The path to the file to upload
- `chat_id`: The channel or user ID to send the file to
- `title`: The title of the file
- `ts`: (Optional) Thread timestamp if replying to a thread

**Example:**
```python
send_file_to_slack("/tmp/report.pdf", "C12345", "Quarterly Report")
```

**Example Usage:**

```
User: Can you generate a PDF report of our sales data?
Maria: I've generated the PDF report and attached it here.
[Sends PDF file to channel]
```

## User and Channel Operations

### Update Slack Users

```python
def update_slack_users()
```

This function updates the local database with current Slack users:

**Example:**
```python
update_slack_users()
```

### Update Slack Conversations

```python
def update_slack_conversations()
```

This function updates the local database with current Slack channels:

**Example:**
```python
update_slack_conversations()
```

### Get Slack User Name

```python
def get_slack_user_name(user_id)
```

This function retrieves a user's name from their ID:

**Parameters:**
- `user_id`: The ID of the user

**Returns:**
- The user's name (real name, display name, or username)

**Example:**
```python
user_name = get_slack_user_name("U12345")
```

## Implementation Details

### Message Sending Implementation

```python
def send_slack_message(message, channel, ts=None):
    """Send a message to a Slack channel or user."""
    try:
        # Prepare message payload
        payload = {
            "channel": channel,
            "text": message
        }
        
        # Add thread ts if provided
        if ts:
            payload["thread_ts"] = ts
        
        # Send message
        response = slack_client.chat_postMessage(**payload)
        
        if not response["ok"]:
            logger.error(f"Error sending message: {response['error']}")
            return False
        
        return response["ts"]
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return False
```

### File Upload Implementation

```python
def send_file_to_slack(file_path, chat_id, title, ts=None):
    """Upload a file to Slack."""
    try:
        # Prepare file upload payload
        payload = {
            "channels": chat_id,
            "file": open(file_path, 'rb'),
            "title": title
        }
        
        # Add thread ts if provided
        if ts:
            payload["thread_ts"] = ts
        
        # Upload file
        response = slack_client.files_upload_v2(**payload)
        
        if not response["ok"]:
            logger.error(f"Error uploading file: {response['error']}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return False
```

### Audio Message Implementation

```python
def send_audio_to_slack(text, chat_id=None, ts=None):
    """Convert text to audio and send to Slack."""
    try:
        # Convert text to speech
        audio_file = text_to_speech(text)
        
        # Upload audio to Slack
        return send_file_to_slack(audio_file, chat_id, "Audio Message", ts)
    except Exception as e:
        logger.error(f"Error sending audio: {str(e)}")
        return False
```

## Slack Event Processing

The Slack integration module also processes incoming Slack events:

```python
def process_slack_event(event):
    """Process a Slack event."""
    event_type = event.get("type")
    
    if event_type == "message":
        return process_message_event(event)
    elif event_type == "app_mention":
        return process_mention_event(event)
    else:
        logger.info(f"Unhandled event type: {event_type}")
        return None
```

## Slack API Client

The module uses the Slack SDK to interact with the Slack API:

```python
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Initialize Slack client
slack_client = WebClient(token=SLACK_BOT_TOKEN)
```

## Error Handling

The module includes comprehensive error handling:

```python
def handle_slack_error(error, operation):
    """Handle Slack API errors."""
    if isinstance(error, SlackApiError):
        if error.response["error"] == "ratelimited":
            # Handle rate limiting
            retry_after = int(error.response.headers.get("Retry-After", 1))
            logger.warning(f"Rate limited. Retrying after {retry_after} seconds.")
            time.sleep(retry_after)
            return True  # Retry
        else:
            # Log other API errors
            logger.error(f"Slack API error during {operation}: {error.response['error']}")
    else:
        # Log general errors
        logger.error(f"Error during {operation}: {str(error)}")
    
    return False  # Don't retry
```

## Best Practices

When working with the Slack integration:

- Handle rate limiting appropriately
- Implement proper error handling
- Keep user and channel information up to date
- Use thread timestamps consistently
- Format messages for readability
- Consider file size limitations

## Future Enhancements

Planned enhancements for Slack integration include:

- Enhanced message formatting
- Interactive message components
- Slash command support
- Event subscription improvements
- Multi-workspace support

---

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [← Conversation Management](conversation-management.md) | [Storage Operations →](storage-operations.md)