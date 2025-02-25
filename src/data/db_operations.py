import time
import json
from decimal import Decimal
from typing import Dict, List, Optional, Any
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from ..core.config import (
    USER_TABLE,
    ASSISTANT_TABLE,
    NAMES_TABLE,
    CHANNELS_TABLE,
    MEETINGS_TABLE
)
from ..core.error_handlers import DatabaseError, decimal_default

def save_message(table, chat_id: str, text: str, role: str, thread: Optional[str] = None, image_urls: Optional[List[str]] = None) -> None:
    """
    Save a message to the specified DynamoDB table.

    Args:
        table: DynamoDB table object
        chat_id: Chat ID where the message was sent
        text: Message content
        role: Role of the sender (user/assistant)
        thread: Thread timestamp (optional)
        image_urls: List of image URLs (optional)

    Raises:
        DatabaseError: If the save operation fails
    """
    try:
        timestamp = int(time.time())
        sort_key = timestamp  # use timestamp as sort key
        ttl = timestamp + 20 * 24 * 60 * 60  # 20 days

        item = {
            'chat_id': chat_id,
            'sort_key': sort_key,
            'message': text,
            'role': role,
            'ttl': ttl
        }

        # Add thread to the item if it's provided
        if thread is not None:
            item['thread'] = thread
        
        # Add image urls to the item if they are provided
        if image_urls is not None:
            item['image_urls'] = image_urls

        table.put_item(Item=item)
    except ClientError as e:
        raise DatabaseError(
            message="Failed to save message",
            status_code=500,
            details={"error": str(e)}
        )

def get_last_messages(table, chat_id: str, num_messages: int) -> List[Dict[str, Any]]:
    """
    Retrieve the last N messages from a DynamoDB table for a specific chat.

    Args:
        table: DynamoDB table object
        chat_id: Chat ID to retrieve messages from
        num_messages: Number of messages to retrieve

    Returns:
        List of message items

    Raises:
        DatabaseError: If the query operation fails
    """
    try:
        response = table.query(
            KeyConditionExpression=Key('chat_id').eq(chat_id),
            Limit=num_messages,
            ScanIndexForward=False  # get the latest messages first
        )
        return response.get('Items', [])
    except ClientError as e:
        raise DatabaseError(
            message="Failed to retrieve messages",
            status_code=500,
            details={"error": str(e)}
        )

def get_message_by_sort_id(role: str, chat_id: str, sort_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a specific message by its sort ID.

    Args:
        role: Role to determine which table to query (user/assistant)
        chat_id: Chat ID of the message
        sort_id: Sort ID of the message

    Returns:
        Message item if found, None otherwise

    Raises:
        DatabaseError: If the query operation fails
    """
    try:
        # Determine the appropriate table based on the role 
        table = USER_TABLE if role == 'user' else ASSISTANT_TABLE

        response = table.query(
            KeyConditionExpression=Key('chat_id').eq(chat_id) & Key('sort_key').eq(sort_id),
            Limit=1
        )
        return response['Items'][0] if response.get('Items') else None
    except ClientError as e:
        raise DatabaseError(
            message="Failed to retrieve message",
            status_code=500,
            details={"error": str(e)}
        )

def get_messages_in_range(chat_id: str, start_sort_id: int, end_sort_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve messages within a specific sort ID range from both user and assistant tables.

    Args:
        chat_id: Chat ID to retrieve messages from
        start_sort_id: Starting sort ID
        end_sort_id: Ending sort ID

    Returns:
        List of messages sorted by sort_key

    Raises:
        DatabaseError: If the query operation fails
    """
    try:
        def query_table(table):
            response = table.query(
                KeyConditionExpression=Key('chat_id').eq(chat_id) & 
                                     Key('sort_key').between(start_sort_id, end_sort_id)
            )
            return response.get('Items', [])

        # Retrieve messages from both tables
        user_messages = query_table(USER_TABLE)
        assistant_messages = query_table(ASSISTANT_TABLE)

        # Combine and sort messages by sort_key
        all_messages = user_messages + assistant_messages
        all_messages.sort(key=lambda x: x['sort_key'])
        
        return all_messages
    except ClientError as e:
        raise DatabaseError(
            message="Failed to retrieve messages in range",
            status_code=500,
            details={"error": str(e)}
        )

def convert_floats_to_decimals(obj: Any) -> Any:
    """
    Convert float values to Decimal for DynamoDB compatibility.

    Args:
        obj: Object to convert

    Returns:
        Object with float values converted to Decimal
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimals(v) for v in obj]
    return obj

def serialize_message(message: Dict[str, Any]) -> str:
    """
    Serialize a message dictionary to JSON string, handling Decimal types.

    Args:
        message: Message dictionary to serialize

    Returns:
        JSON string representation of the message
    """
    try:
        return json.dumps(message, default=decimal_default)
    except (TypeError, ValueError) as e:
        raise DatabaseError(
            message="Failed to serialize message",
            status_code=500,
            details={"error": str(e)}
        )