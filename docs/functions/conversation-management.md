# Conversation Management

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [← Lambda Function](lambda-function.md) | [Storage Operations →](storage-operations.md)

The conversation management module in `conversation.py` handles the formatting and processing of conversations between users and the Maria AI Assistant.

## Overview

The conversation management module is responsible for:

- Formatting conversations for the AI model
- Creating appropriate prompts based on context
- Handling different conversation types (text, vision, audio)
- Making API calls to OpenAI
- Processing and formatting responses

## Key Functions

### Text Conversation Formatting

```python
def make_text_conversation(system_text, assistant_text, display_name, msg_history_summary, all_messages, text)
```

This function formats a conversation with text only:

**Parameters:**
- `system_text`: The system instructions
- `assistant_text`: The assistant persona description
- `display_name`: The user's display name
- `msg_history_summary`: A summary of the message history
- `all_messages`: All relevant messages in the conversation
- `text`: The current message text

**Example:**
```python
conversation = make_text_conversation(
    system_text="You are Maria, an AI assistant...",
    assistant_text="I'm Maria, your friendly AI assistant...",
    display_name="John",
    msg_history_summary="Discussion about project timeline",
    all_messages=[...],
    text="When is the project deadline?"
)
```

### Vision Conversation Formatting

```python
def make_vision_conversation(system_text, assistant_text, display_name, all_relevant_messages, msg_history_summary, all_messages, text, image_urls=None)
```

This function formats a conversation with images:

**Parameters:**
- `system_text`: The system instructions
- `assistant_text`: The assistant persona description
- `display_name`: The user's display name
- `all_relevant_messages`: Semantically relevant past messages
- `msg_history_summary`: A summary of the message history
- `all_messages`: All messages in the conversation
- `text`: The current message text
- `image_urls`: (Optional) List of image URLs

**Example:**
```python
conversation = make_vision_conversation(
    system_text="You are Maria, an AI assistant...",
    assistant_text="I'm Maria, your friendly AI assistant...",
    display_name="John",
    all_relevant_messages=[...],
    msg_history_summary="Discussion about product design",
    all_messages=[...],
    text="What do you think of this design?",
    image_urls=["https://example.com/image.jpg"]
)
```

### Audio Conversation Formatting

```python
def make_audio_conversation(system_text, assistant_text, display_name, all_relevant_messages, msg_history_summary, all_messages, text, audio_urls=None)
```

This function formats a conversation with audio:

**Parameters:**
- `system_text`: The system instructions
- `assistant_text`: The assistant persona description
- `display_name`: The user's display name
- `all_relevant_messages`: Semantically relevant past messages
- `msg_history_summary`: A summary of the message history
- `all_messages`: All messages in the conversation
- `text`: The current message text
- `audio_urls`: (Optional) List of audio URLs

**Example:**
```python
conversation = make_audio_conversation(
    system_text="You are Maria, an AI assistant...",
    assistant_text="I'm Maria, your friendly AI assistant...",
    display_name="John",
    all_relevant_messages=[...],
    msg_history_summary="Discussion about meeting notes",
    all_messages=[...],
    text="Here's the recording from yesterday's meeting",
    audio_urls=["https://example.com/audio.mp3"]
)
```

### OpenAI API Calls

```python
def make_openai_vision_call(client, conversations)
def make_openai_audio_call(client, conversations)
def ask_openai_o1(prompt)
```

These functions make API calls to OpenAI:

**Parameters:**
- `client`: The OpenAI client
- `conversations`: The formatted conversation
- `prompt`: The prompt text (for `ask_openai_o1`)

**Example:**
```python
# Vision call
response = make_openai_vision_call(openai_client, vision_conversation)

# Audio call
response = make_openai_audio_call(openai_client, audio_conversation)

# Simple text call
response = ask_openai_o1("Summarize the following text: ...")
```

## Conversation Structure

The conversation structure follows this format:

```python
{
    "messages": [
        {
            "role": "system",
            "content": system_text
        },
        {
            "role": "assistant",
            "content": assistant_text
        },
        # Message history
        {
            "role": "user",
            "content": "Previous user message"
        },
        {
            "role": "assistant",
            "content": "Previous assistant response"
        },
        # Current message
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": current_text
                },
                # Optional image content
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url
                    }
                }
            ]
        }
    ]
}
```

## Implementation Details

### Text Conversation Implementation

```python
def make_text_conversation(system_text, assistant_text, display_name, msg_history_summary, all_messages, text):
    """Format a conversation with text only."""
    messages = [
        {"role": "system", "content": system_text},
        {"role": "assistant", "content": assistant_text}
    ]
    
    # Add message history
    for msg in all_messages:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Add current message
    messages.append({
        "role": "user",
        "content": text
    })
    
    return {"messages": messages}
```

### Vision Conversation Implementation

```python
def make_vision_conversation(system_text, assistant_text, display_name, all_relevant_messages, msg_history_summary, all_messages, text, image_urls=None):
    """Format a conversation with images."""
    messages = [
        {"role": "system", "content": system_text},
        {"role": "assistant", "content": assistant_text}
    ]
    
    # Add message history
    for msg in all_messages:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Add current message with images
    content = [{"type": "text", "text": text}]
    
    if image_urls:
        for url in image_urls:
            content.append({
                "type": "image_url",
                "image_url": {"url": url}
            })
    
    messages.append({
        "role": "user",
        "content": content
    })
    
    return {"messages": messages}
```

## Best Practices

When working with conversation management:

- Keep system prompts clear and concise
- Include relevant context but avoid excessive history
- Format conversations consistently
- Handle different content types appropriately
- Implement proper error handling for API calls

## Future Enhancements

Planned enhancements for conversation management include:

- Enhanced context summarization
- Dynamic system prompt selection
- Multi-modal conversation improvements
- Conversation state management
- Performance optimizations for large conversations

---

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [← Lambda Function](lambda-function.md) | [Storage Operations →](storage-operations.md)