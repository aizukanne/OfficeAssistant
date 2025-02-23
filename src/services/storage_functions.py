from typing import Dict, List, Tuple, Optional
from src.services.storage_service import get_instance

def save_message(chat_id: str, text: str, role: str, thread: Optional[str] = None, image_urls: Optional[List[str]] = None) -> bool:
    """Save a message to DynamoDB."""
    return get_instance().save_message(chat_id, text, role, thread, image_urls)

def get_last_messages(chat_id: str, num_messages: int, table: str) -> List[Dict]:
    """Get last N messages from DynamoDB."""
    return get_instance().get_last_messages(chat_id, num_messages, table)

def get_message_by_sort_id(chat_id: str, sort_id: int, table: str) -> Optional[Dict]:
    """Get message by sort ID."""
    return get_instance().get_message_by_sort_id(chat_id, sort_id, table)

def get_messages_in_range(chat_id: str, start_sort_id: int, end_sort_id: int) -> List[Dict]:
    """Get messages within a sort ID range."""
    return get_instance().get_messages_in_range(chat_id, start_sort_id, end_sort_id)

def upload_to_s3(bucket: str, file_data: bytes, file_key: str, content_type: Optional[str] = None) -> str:
    """Upload a file to S3."""
    return get_instance().upload_to_s3(bucket, file_data, file_key, content_type)

def download_from_s3(bucket: str, file_key: str) -> bytes:
    """Download a file from S3."""
    return get_instance().download_from_s3(bucket, file_key)

def delete_from_s3(bucket: str, file_key: str) -> bool:
    """Delete a file from S3."""
    return get_instance().delete_from_s3(bucket, file_key)

def list_s3_files(bucket: str, prefix: Optional[str] = None) -> List[str]:
    """List files in an S3 bucket."""
    return get_instance().list_s3_files(bucket, prefix)

def find_image_urls(messages: List[Dict]) -> Tuple[bool, List[str]]:
    """Find image URLs in messages."""
    return get_instance().find_image_urls(messages)