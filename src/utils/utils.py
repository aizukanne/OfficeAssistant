import re
import json
from typing import Any, Dict, Union, Optional
from decimal import Decimal
from bson import ObjectId

def decimal_default(obj: Any) -> Any:
    """
    JSON serializer for objects not serializable by default json code.

    Args:
        obj: Object to serialize

    Returns:
        JSON serializable version of the object

    Raises:
        TypeError: If object cannot be serialized
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def convert_floats_to_decimals(obj: Any) -> Any:
    """
    Convert float values to Decimal for DynamoDB compatibility.

    Args:
        obj: Object containing float values

    Returns:
        Object with floats converted to Decimals
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimals(v) for v in obj]
    return obj

def replace_problematic_chars(text: str) -> str:
    """
    Replace common problematic Unicode characters with ASCII equivalents.

    Args:
        text: Text containing Unicode characters

    Returns:
        Text with problematic characters replaced
    """
    replacements = {
        '\u2018': "'",  # Left single quotation mark
        '\u2019': "'",  # Right single quotation mark
        '\u201c': '"',  # Left double quotation mark
        '\u201d': '"',  # Right double quotation mark
        '\u2013': '-',  # En dash
        '\u2014': '-',  # Em dash
        '\u2026': '...', # Ellipsis
        '\u2022': '*',  # Bullet point
        '\u00A0': ' ',  # Non-breaking space
        '\u2010': '-',  # Hyphen
        '\u2012': '-',  # Figure dash
        '\u2015': '-',  # Horizontal bar
    }
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)
    return text

def is_serializable(value: Any) -> bool:
    """
    Check if a value is JSON serializable.

    Args:
        value: Value to check

    Returns:
        True if value is serializable, False otherwise
    """
    try:
        json.dumps(value)
        return True
    except (TypeError, OverflowError):
        return False

def solve_maths(code: str, **params) -> Dict[str, Any]:
    """
    Execute mathematical code safely and return the result.

    Args:
        code: Python code to execute
        **params: Additional parameters for the code

    Returns:
        Dictionary containing result or error message
    """
    exec_env = {}
    exec_env.update(params)
    
    try:
        exec(code, {}, exec_env)
        
        # Filter out non-serializable objects
        serializable_result = {
            key: value for key, value in exec_env.items()
            if is_serializable(value)
        }
        
        return {
            "status": "success",
            "result": serializable_result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def clean_website_data(raw_text: str) -> str:
    """
    Clean up raw website text data.

    Args:
        raw_text: Raw text from website

    Returns:
        Cleaned text
    """
    try:
        # Remove HTML tags
        cleaned_text = re.sub('<[^<]+?>', '', raw_text)

        # Remove multiple spaces and newlines
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        # Remove non-printing characters
        cleaned_text = ''.join(c for c in cleaned_text if c.isprintable())
        
        return cleaned_text
    except Exception as e:
        return json.dumps({"error": f"Error processing text: {str(e)}"})

def find_image_urls(data: list) -> tuple[bool, list]:
    """
    Find all image URLs in message data.

    Args:
        data: List of message dictionaries

    Returns:
        Tuple of (has_images: bool, image_urls: list)
    """
    image_urls = []
    for item in data:
        if "image_urls" in item:
            image_urls.extend(item["image_urls"])
    return bool(image_urls), image_urls

def message_to_json(message_string: str) -> str:
    """
    Convert message string to JSON format.

    Args:
        message_string: Message string containing JSON blocks

    Returns:
        JSON string
    """
    message_parts = re.split(r'```json|```', message_string)
    
    message = {
        "assistant": f"{message_parts[0].strip()} {message_parts[2].strip()}",
        "blocks": json.loads(message_parts[1])['blocks']
    }
    
    return json.dumps(message)

def normalize_message(response: Any) -> Any:
    """
    Normalize message response to consistent format.

    Args:
        response: API response object

    Returns:
        Normalized message object
    """
    if isinstance(response, dict):
        message = response['choices'][0]['message']
        return type('Message', (), {
            'content': message.get('content'),
            'audio': message.get('audio'),
            'tool_calls': message.get('tool_calls')
        })
    return response.choices[0].message

def safe_json_dumps(obj: Any) -> str:
    """
    Safely convert object to JSON string.

    Args:
        obj: Object to convert

    Returns:
        JSON string
    """
    try:
        return json.dumps(obj, default=decimal_default)
    except (TypeError, ValueError) as e:
        return json.dumps({
            "error": "Could not serialize object",
            "details": str(e)
        })