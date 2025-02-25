import json
from typing import Dict, List, Any, Set
from decimal import Decimal
from bson import ObjectId
from nltk.tokenize import sent_tokenize, word_tokenize
from ..core.error_handlers import decimal_default

def load_stopwords(file_path: str) -> Set[str]:
    """
    Load stopwords from a given file.

    Args:
        file_path: Path to the stopwords file

    Returns:
        Set of stopwords

    Raises:
        FileNotFoundError: If stopwords file not found
        IOError: If error reading file
    """
    try:
        with open(file_path, 'r') as file:
            stopwords = set(file.read().splitlines())
        return stopwords
    except FileNotFoundError:
        raise FileNotFoundError(f"Stopwords file not found at: {file_path}")
    except IOError as e:
        raise IOError(f"Error reading stopwords file: {str(e)}")

def rank_sentences(text: str, stopwords: Set[str], max_sentences: int = 10) -> str:
    """
    Rank sentences in the text based on word frequency, returning top N sentences.

    Args:
        text: Input text to rank
        stopwords: Set of stopwords to exclude
        max_sentences: Maximum number of sentences to return

    Returns:
        String containing top ranked sentences
    """
    # Calculate word frequencies
    word_frequencies = {}
    for word in word_tokenize(text.lower()):
        if word.isalpha() and word not in stopwords:
            word_frequencies[word] = word_frequencies.get(word, 0) + 1

    # Score sentences based on word frequencies
    sentence_scores = {}
    sentences = sent_tokenize(text)
    for sent in sentences:
        if len(sent.split(' ')) < 30:  # Skip very long sentences
            for word in word_tokenize(sent.lower()):
                if word in word_frequencies:
                    sentence_scores[sent] = sentence_scores.get(sent, 0) + word_frequencies[word]

    # Sort sentences by score and take top N
    sorted_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)
    summary_sentences = sorted_sentences[:max_sentences]
    
    # Add a full stop at the end of each sentence if needed
    summary = ' '.join([s if s.endswith('.') else f'{s}.' for s in summary_sentences])
    return summary

def summarize_record(record: str, stopwords: Set[str]) -> Dict[str, Any]:
    """
    Summarize a single message record while maintaining key points and brevity.

    Args:
        record: Record string in format 'sort_key: chat_id: role: message'
        stopwords: Set of stopwords to exclude

    Returns:
        Dictionary containing summarized record
    """
    # Parse record format: 'sort_key: chat_id: role: message'
    parts = record.split(':', 3)
    sort_key, chat_id, role, message = parts[0], parts[1], parts[2], parts[3].strip()
    
    # Summarize the message
    summarized_message = rank_sentences(message, stopwords, max_sentences=5)
    
    return {
        'sort_key': sort_key,
        'chat_id': chat_id,
        'role': role,
        'message_summary': summarized_message
    }

def summarize_messages(data: List[Dict[str, Any]], stopwords: Set[str]) -> List[Dict[str, Any]]:
    """
    Summarize messages from a dictionary and return a dictionary with the summarized conversation.

    Args:
        data: List of message dictionaries
        stopwords: Set of stopwords to exclude

    Returns:
        List of summarized message records
    """
    # Create play-like records
    records = [
        f"{item['sort_key']}: {item['chat_id']}: {item['role']}: {item['message']}" 
        for item in data
    ]
    
    # Summarize each record
    summarized_records = [summarize_record(record, stopwords) for record in records]
    return summarized_records

def clean_website_data(raw_text: str) -> str:
    """
    Cleans up raw website text data, removing common HTML artifacts and excess whitespace.

    Args:
        raw_text: Raw text from website

    Returns:
        Cleaned text string
    """
    try:
        # Remove HTML tags (basic HTML tag removal)
        cleaned_text = re.sub('<[^<]+?>', '', raw_text)

        # Remove multiple spaces and newlines, and then trim
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        # Remove non-printing characters
        cleaned_text = ''.join(c for c in cleaned_text if c.isprintable())
        
        return cleaned_text
    except Exception as e:
        return json.dumps({"error": f"Error processing text: {str(e)}"})

def find_image_urls(data: List[Dict[str, Any]]) -> tuple[bool, List[str]]:
    """
    Find all image URLs in a list of message data.

    Args:
        data: List of message dictionaries

    Returns:
        Tuple of (has_images: bool, image_urls: List[str])
    """
    image_urls = []
    for item in data:
        if "image_urls" in item:
            image_urls.extend(item["image_urls"])
    return bool(image_urls), image_urls

def message_to_json(message_string: str) -> str:
    """
    Convert a message string containing JSON blocks to a structured JSON format.

    Args:
        message_string: Message string containing JSON blocks

    Returns:
        JSON string containing formatted message
    """
    message_parts = re.split(r'```json|```', message_string)
    
    message = {
        "assistant": f"{message_parts[0].strip()} {message_parts[2].strip()}",
        "blocks": json.loads(message_parts[1])['blocks']
    }
    
    return json.dumps(message)

def normalize_message(response: Any) -> Any:
    """
    Normalize message response to a consistent format regardless of input type.

    Args:
        response: Response object from API

    Returns:
        Normalized message object
    """
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