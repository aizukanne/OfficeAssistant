import json
from typing import Dict, List, Any, Optional
from ..core.error_handlers import decimal_default

def make_text_conversation(
    system_text: str,
    assistant_text: str,
    display_name: Optional[str],
    msg_history_summary: List[Dict[str, Any]],
    all_messages: List[Dict[str, Any]],
    text: str
) -> List[Dict[str, Any]]:
    """
    Create a conversation array for text-based interactions.

    Args:
        system_text: System prompt text
        assistant_text: Assistant's initial message
        display_name: User's display name
        msg_history_summary: Summary of message history
        all_messages: All previous messages
        text: Current user message

    Returns:
        List of conversation messages
    """
    # Initialize conversation array
    conversation = [
        {"role": "system", "content": system_text},
        {"role": "assistant", "content": assistant_text}
    ]

    # Add message history summary
    conversation.append({
        "role": "assistant",
        "content": json.dumps(msg_history_summary, default=decimal_default)
    })
    
    # Add previous messages to the conversation array
    for message in all_messages:
        conversation.append({
            "role": message['role'],
            "content": message['message']
        })

    # Add transition message
    conversation.append({
        "role": "assistant",
        "content": "All the previous messages are a trail of the message history to aid your understanding of the conversation. The next message is the current request from the user."
    })
    
    # Add user message with optional display name
    user_message = {
        "role": "user",
        "content": text
    }
    if display_name:
        user_message["name"] = display_name
    conversation.append(user_message)

    return conversation

def make_vision_conversation(
    system_text: str,
    assistant_text: str,
    display_name: Optional[str],
    msg_history_summary: List[Dict[str, Any]],
    all_messages: List[Dict[str, Any]],
    text: str,
    image_urls: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Create a conversation array for vision-based interactions.

    Args:
        system_text: System prompt text
        assistant_text: Assistant's initial message
        display_name: User's display name
        msg_history_summary: Summary of message history
        all_messages: All previous messages
        text: Current user message
        image_urls: Optional list of image URLs

    Returns:
        List of conversation messages
    """
    # Initialize conversation array
    conversation = [
        {
            "role": "system",
            "content": [{"type": "text", "text": system_text}]
        },
        {
            "role": "assistant",
            "content": [{"type": "text", "text": assistant_text}]
        }
    ]

    # Add message history summary
    conversation.append({
        "role": "assistant",
        "content": [{
            "type": "text",
            "text": json.dumps(msg_history_summary, default=decimal_default)
        }]
    })
    
    # Add previous messages with their images
    for message in all_messages:
        content = [{"type": "text", "text": message['message']}]
        
        # Add any image URLs from previous messages
        if "image_urls" in message:
            for url in message["image_urls"]:
                if url:  # Ensure URL is not empty
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": url}
                    })
        
        conversation.append({
            "role": message['role'],
            "content": content
        })

    # Add transition message
    conversation.append({
        "role": "assistant",
        "content": "All the previous messages are a trail of the message history to aid your understanding of the conversation. The next message is the current request from the user."
    })

    # Add user message with optional images
    user_content = [{"type": "text", "text": text}]
    if image_urls:
        for url in image_urls:
            if url:  # Check if URL is not empty
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": url}
                })

    # Create user message with optional display name
    user_message = {
        "role": "user",
        "content": user_content
    }
    if display_name:
        user_message["name"] = display_name
    conversation.append(user_message)

    return conversation

def make_audio_conversation(
    system_text: str,
    assistant_text: str,
    display_name: Optional[str],
    msg_history_summary: List[Dict[str, Any]],
    all_messages: List[Dict[str, Any]],
    text: str,
    audio_urls: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Create a conversation array for audio-based interactions.

    Args:
        system_text: System prompt text
        assistant_text: Assistant's initial message
        display_name: User's display name
        msg_history_summary: Summary of message history
        all_messages: All previous messages
        text: Current user message
        audio_urls: Optional list of audio URLs

    Returns:
        List of conversation messages
    """
    # Initialize conversation array
    conversation = [
        {
            "role": "system",
            "content": [{"type": "text", "text": system_text}]
        },
        {
            "role": "assistant",
            "content": [{"type": "text", "text": assistant_text}]
        }
    ]

    # Add message history summary
    conversation.append({
        "role": "assistant",
        "content": [{"type": "text", "text": json.dumps(msg_history_summary)}]
    })

    # Add previous messages
    for message in all_messages:
        content = [{"type": "text", "text": message["message"]}]
        conversation.append({
            "role": message["role"],
            "content": content
        })

    # Add transition message
    conversation.append({
        "role": "assistant",
        "content": "All the previous messages are a trail of the message history to aid your understanding of the conversation. The next message is the current request from the user."
    })

    # Add user message with optional audio
    user_content = [{"type": "text", "text": text}]
    if audio_urls:
        for url in audio_urls:
            if url:
                # Download and encode the audio file
                response = requests.get(url)
                response.raise_for_status()
                m4a_data = response.content

                # Convert M4A data to WAV in memory
                wav_data = convert_to_wav_in_memory(m4a_data)  # This needs to be imported from audio_processing
                encoded_string = base64.b64encode(wav_data).decode("utf-8")

                user_content.append({
                    "type": "input_audio",
                    "input_audio": {
                        "data": encoded_string,
                        "format": "wav"
                    }
                })

    # Create user message with optional display name
    user_message = {
        "role": "user",
        "content": user_content
    }
    if display_name:
        user_message["name"] = display_name
    conversation.append(user_message)

    return conversation