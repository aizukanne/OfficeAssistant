import json
from typing import List, Dict, Any, Optional
from decimal import Decimal

def summarize_messages(messages: List[Dict]) -> Dict:
    """
    Creates a summary of a list of messages.
    
    Args:
        messages: List of messages to summarize
        
    Returns:
        Dict: Summary of the messages
    """
    if not messages:
        return {"summary": "No message history available."}
        
    # Extract key information
    message_count = len(messages)
    unique_roles = set(msg['role'] for msg in messages)
    
    # Create a brief summary
    summary = {
        "message_count": message_count,
        "participants": list(unique_roles),
        "time_range": {
            "start": messages[0]['sort_key'],
            "end": messages[-1]['sort_key']
        }
    }
    
    return summary

def decimal_default(obj: Any) -> Any:
    """
    JSON serializer for objects not serializable by default json code.
    
    Args:
        obj: Object to serialize
        
    Returns:
        Any: Serialized object
    """
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def load_stopwords(language: str) -> List[str]:
    """
    Loads stopwords for the specified language.
    
    Args:
        language: Language code (e.g., 'english')
        
    Returns:
        List[str]: List of stopwords
    """
    # This is a placeholder - actual implementation would need to:
    # 1. Load stopwords from a file or database
    # 2. Process and return them
    return []

def clean_text(text: str) -> str:
    """
    Cleans and normalizes text.
    
    Args:
        text: Text to clean
        
    Returns:
        str: Cleaned text
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters (keep alphanumeric and spaces)
    text = ''.join(c for c in text if c.isalnum() or c.isspace())
    
    return text

def extract_keywords(text: str, stopwords: List[str]) -> List[str]:
    """
    Extracts keywords from text.
    
    Args:
        text: Text to extract keywords from
        stopwords: List of stopwords to exclude
        
    Returns:
        List[str]: List of keywords
    """
    # Clean the text
    cleaned_text = clean_text(text)
    
    # Split into words
    words = cleaned_text.split()
    
    # Remove stopwords
    keywords = [word for word in words if word not in stopwords]
    
    return keywords

def find_urls(text: str) -> List[str]:
    """
    Finds URLs in text.
    
    Args:
        text: Text to search for URLs
        
    Returns:
        List[str]: List of found URLs
    """
    import re
    
    # URL pattern
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    
    # Find all matches
    urls = re.findall(url_pattern, text)
    
    return urls

def truncate_text(text: str, max_length: int, suffix: str = '...') -> str:
    """
    Truncates text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add to truncated text
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
        
    return text[:max_length - len(suffix)] + suffix

def format_message_for_display(
    message: Dict,
    include_metadata: bool = False
) -> str:
    """
    Formats a message for display.
    
    Args:
        message: Message dictionary to format
        include_metadata: Whether to include metadata
        
    Returns:
        str: Formatted message
    """
    text = message.get('message', '')
    
    if include_metadata:
        role = message.get('role', 'unknown')
        timestamp = message.get('sort_key', 0)
        
        metadata = f"[{role}] [{timestamp}] "
        text = metadata + text
        
    return text

def parse_command_args(text: str) -> Dict[str, str]:
    """
    Parses command arguments from text.
    
    Args:
        text: Text containing command arguments
        
    Returns:
        Dict[str, str]: Dictionary of parsed arguments
    """
    args = {}
    
    # Split text into words
    words = text.split()
    
    # Look for key=value pairs
    for word in words:
        if '=' in word:
            key, value = word.split('=', 1)
            args[key.strip()] = value.strip()
            
    return args

def generate_chat_summary(
    messages: List[Dict],
    max_length: Optional[int] = None
) -> str:
    """
    Generates a summary of a chat conversation.
    
    Args:
        messages: List of messages to summarize
        max_length: Optional maximum length of summary
        
    Returns:
        str: Chat summary
    """
    if not messages:
        return "No messages to summarize."
        
    # Count messages by role
    role_counts = {}
    for msg in messages:
        role = msg.get('role', 'unknown')
        role_counts[role] = role_counts.get(role, 0) + 1
        
    # Create summary
    summary = "Chat Summary:\n"
    summary += f"Total Messages: {len(messages)}\n"
    
    for role, count in role_counts.items():
        summary += f"{role.capitalize()}: {count} messages\n"
        
    if max_length:
        summary = truncate_text(summary, max_length)
        
    return summary

def serialize_for_json(obj: Any) -> Any:
    """
    Serializes objects for JSON encoding.
    
    Args:
        obj: Object to serialize
        
    Returns:
        Any: JSON-serializable object
    """
    if isinstance(obj, Decimal):
        return str(obj)
    elif isinstance(obj, set):
        return list(obj)
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return str(obj)