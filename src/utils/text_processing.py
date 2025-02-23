import json
import nltk
import os
from typing import List, Dict, Any, Optional
from decimal import Decimal
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords as nltk_stopwords
from src.config.settings import NLTK_CONFIG
from src.core.exceptions import DataProcessingError
from src.core.logging import ServiceLogger

# Initialize logger
logger = ServiceLogger('text_processing')

def ensure_nltk_data():
    """
    Verifies NLTK data is available.
    - punkt and punkt_tab are in Lambda layer at /opt/nltk_data/tokenizers
    - stopwords are in project root at /var/task/stopwords
    """
    # Set paths for NLTK data
    nltk.data.path = ['/opt/nltk_data']  # Lambda layer path for tokenizers
    
    # Verify punkt is available
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        logger.error("punkt tokenizer not found in Lambda layer")
        raise DataProcessingError(
            "Required NLTK punkt tokenizer missing. "
            "Ensure punkt is included in the Lambda layer at /opt/nltk_data/tokenizers"
        )

def load_stopwords(language: str = 'english') -> List[str]:
    """
    Loads stopwords from project root.
    
    Args:
        language: Language code (e.g., 'english')
        
    Returns:
        List[str]: List of stopwords
        
    Raises:
        DataProcessingError: If stopwords cannot be loaded
    """
    try:
        # Verify punkt tokenizer is available
        ensure_nltk_data()
        
        # Load stopwords from project root (next to src directory)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        stopwords_path = os.path.join(project_root, 'stopwords', language)
        if not os.path.exists(stopwords_path):
            raise DataProcessingError(f"Stopwords file not found for language: {language}")
            
        with open(stopwords_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Failed to load stopwords for language: {language}", error=str(e))
        raise DataProcessingError(f"Failed to load stopwords: {str(e)}")

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
    words = word_tokenize(cleaned_text)
    
    # Remove stopwords
    keywords = [word for word in words if word not in stopwords]
    
    return keywords

def rank_sentences(text: str, stopwords: List[str], max_sentences: int = 10) -> str:
    """
    Ranks sentences in text based on word frequency, returning top N sentences.
    
    Args:
        text: Text to rank sentences from
        stopwords: List of stopwords to exclude
        max_sentences: Maximum number of sentences to return
        
    Returns:
        str: Ranked sentences joined into text
        
    Raises:
        DataProcessingError: If sentence ranking fails
    """
    try:
        ensure_nltk_data()
        
        # Get word frequencies
        word_frequencies = {}
        for word in word_tokenize(text.lower()):
            if word.isalpha() and word not in stopwords:
                word_frequencies[word] = word_frequencies.get(word, 0) + 1

        # Score sentences
        sentence_scores = {}
        sentences = sent_tokenize(text)
        for sent in sentences:
            for word in word_tokenize(sent.lower()):
                if word in word_frequencies and len(sent.split(' ')) < 30:
                    sentence_scores[sent] = sentence_scores.get(sent, 0) + word_frequencies[word]

        # Get top sentences
        sorted_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)
        summary_sentences = sorted_sentences[:max_sentences]
        
        # Add periods if missing
        summary = ' '.join([s if s.endswith('.') else f'{s}.' for s in summary_sentences])

        return summary
    except Exception as e:
        logger.error("Failed to rank sentences", error=str(e))
        raise DataProcessingError(f"Failed to rank sentences: {str(e)}")

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

def summarize_messages(
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

def decimal_default(obj: Any) -> Any:
    """
    JSON encoder for Decimal objects.
    
    Args:
        obj: Object to encode
        
    Returns:
        Any: JSON-serializable object
    """
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

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

# Initialize NLTK data on module load
try:
    ensure_nltk_data()
except Exception as e:
    logger.error("Failed to initialize NLTK data", error=str(e))