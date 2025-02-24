"""Public storage service functions."""
from typing import Dict, List, Optional, Tuple, Any
from src.utils.logging import log_message, log_error
from src.utils.decorators import log_function_call, log_error_decorator
from src.utils.error_handling import wrap_exceptions, handle_service_error
from src.core.exceptions import StorageError, ValidationError
from .service import get_instance

@log_function_call('storage')
@wrap_exceptions(StorageError, operation='save_message')
def save_message(
    chat_id: str,
    text: str,
    role: str,
    thread: Optional[str] = None,
    image_urls: Optional[List[str]] = None
) -> bool:
    """
    Save a message to DynamoDB.
    
    Args:
        chat_id: Chat identifier
        text: Message text
        role: Message role (user/assistant)
        thread: Optional thread identifier
        image_urls: Optional list of image URLs
        
    Returns:
        bool: Success status
        
    Raises:
        StorageError: If save operation fails
        ValidationError: If parameters are invalid
    """
    if not chat_id or not text or not role:
        raise ValidationError(
            "Missing required parameters",
            chat_id=bool(chat_id),
            text=bool(text),
            role=bool(role)
        )
    
    log_message('INFO', 'storage', 'Saving message via function',
               chat_id=chat_id, role=role)
    return get_instance().save_message(chat_id, text, role, thread, image_urls)

@log_function_call('storage')
@wrap_exceptions(StorageError, operation='get_last_messages')
def get_last_messages(
    chat_id: str,
    num_messages: int,
    table: str
) -> List[Dict]:
    """
    Get last N messages from DynamoDB.
    
    Args:
        chat_id: Chat identifier
        num_messages: Number of messages to retrieve
        table: Table name
        
    Returns:
        List[Dict]: List of messages
        
    Raises:
        StorageError: If retrieval fails
        ValidationError: If parameters are invalid
    """
    if not chat_id or num_messages < 1:
        raise ValidationError(
            "Invalid parameters",
            chat_id=bool(chat_id),
            num_messages=num_messages
        )
    
    log_message('INFO', 'storage', 'Getting last messages via function',
               chat_id=chat_id, num_messages=num_messages)
    return get_instance().get_last_messages(chat_id, num_messages, table)

@log_function_call('storage')
@wrap_exceptions(StorageError, operation='get_message_by_sort_id')
def get_message_by_sort_id(
    chat_id: str,
    sort_id: int,
    table: str
) -> Optional[Dict]:
    """
    Get message by sort ID.
    
    Args:
        chat_id: Chat identifier
        sort_id: Sort ID
        table: Table name
        
    Returns:
        Optional[Dict]: Message if found
        
    Raises:
        StorageError: If retrieval fails
        ValidationError: If parameters are invalid
    """
    if not chat_id or sort_id < 0:
        raise ValidationError(
            "Invalid parameters",
            chat_id=bool(chat_id),
            sort_id=sort_id
        )
    
    log_message('INFO', 'storage', 'Getting message by sort ID via function',
               chat_id=chat_id, sort_id=sort_id)
    return get_instance().retrieve(chat_id, sort_id=sort_id, table=table)

@log_function_call('storage')
@wrap_exceptions(StorageError, operation='get_messages_in_range')
def get_messages_in_range(
    chat_id: str,
    start_sort_id: int,
    end_sort_id: int
) -> List[Dict]:
    """
    Get messages within a sort ID range.
    
    Args:
        chat_id: Chat identifier
        start_sort_id: Start sort ID
        end_sort_id: End sort ID
        
    Returns:
        List[Dict]: List of messages
        
    Raises:
        StorageError: If retrieval fails
        ValidationError: If parameters are invalid
    """
    if not chat_id or start_sort_id < 0 or end_sort_id < start_sort_id:
        raise ValidationError(
            "Invalid parameters",
            chat_id=bool(chat_id),
            start_sort_id=start_sort_id,
            end_sort_id=end_sort_id
        )
    
    log_message('INFO', 'storage', 'Getting messages in range via function',
               chat_id=chat_id, start=start_sort_id, end=end_sort_id)
    return get_instance().get_messages_in_range(chat_id, start_sort_id, end_sort_id)

@log_function_call('storage')
@wrap_exceptions(StorageError, operation='upload_to_s3')
def upload_to_s3(
    bucket: str,
    file_data: bytes,
    file_key: str,
    content_type: Optional[str] = None
) -> str:
    """
    Upload a file to S3.
    
    Args:
        bucket: Bucket identifier
        file_data: File content
        file_key: File key
        content_type: Optional content type
        
    Returns:
        str: S3 URL
        
    Raises:
        StorageError: If upload fails
        ValidationError: If parameters are invalid
    """
    if not bucket or not file_data or not file_key:
        raise ValidationError(
            "Missing required parameters",
            bucket=bool(bucket),
            file_data=bool(file_data),
            file_key=bool(file_key)
        )
    
    log_message('INFO', 'storage', 'Uploading to S3 via function',
               bucket=bucket, key=file_key)
    return get_instance().upload_to_s3(bucket, file_data, file_key, content_type)

@log_function_call('storage')
@wrap_exceptions(StorageError, operation='download_from_s3')
def download_from_s3(
    bucket: str,
    file_key: str
) -> bytes:
    """
    Download a file from S3.
    
    Args:
        bucket: Bucket identifier
        file_key: File key
        
    Returns:
        bytes: File content
        
    Raises:
        StorageError: If download fails
        ValidationError: If parameters are invalid
    """
    if not bucket or not file_key:
        raise ValidationError(
            "Missing required parameters",
            bucket=bool(bucket),
            file_key=bool(file_key)
        )
    
    log_message('INFO', 'storage', 'Downloading from S3 via function',
               bucket=bucket, key=file_key)
    return get_instance().download_from_s3(bucket, file_key)

@log_function_call('storage')
@wrap_exceptions(StorageError, operation='delete_from_s3')
def delete_from_s3(
    bucket: str,
    file_key: str
) -> bool:
    """
    Delete a file from S3.
    
    Args:
        bucket: Bucket identifier
        file_key: File key
        
    Returns:
        bool: Success status
        
    Raises:
        StorageError: If deletion fails
        ValidationError: If parameters are invalid
    """
    if not bucket or not file_key:
        raise ValidationError(
            "Missing required parameters",
            bucket=bool(bucket),
            file_key=bool(file_key)
        )
    
    log_message('INFO', 'storage', 'Deleting from S3 via function',
               bucket=bucket, key=file_key)
    return get_instance().delete_from_s3(bucket, file_key)

@log_function_call('storage')
@wrap_exceptions(StorageError, operation='list_s3_files')
def list_s3_files(
    bucket: str,
    prefix: Optional[str] = None
) -> List[str]:
    """
    List files in an S3 bucket.
    
    Args:
        bucket: Bucket identifier
        prefix: Optional prefix filter
        
    Returns:
        List[str]: List of file keys
        
    Raises:
        StorageError: If listing fails
        ValidationError: If parameters are invalid
    """
    if not bucket:
        raise ValidationError("Bucket identifier is required")
    
    log_message('INFO', 'storage', 'Listing S3 files via function',
               bucket=bucket, prefix=prefix)
    return get_instance().list_s3_files(bucket, prefix)

@log_function_call('storage')
@wrap_exceptions(StorageError, operation='find_image_urls')
def find_image_urls(
    messages: List[Dict]
) -> Tuple[bool, List[str]]:
    """
    Find image URLs in messages.
    
    Args:
        messages: List of messages
        
    Returns:
        Tuple[bool, List[str]]: Has images flag and list of URLs
        
    Raises:
        StorageError: If processing fails
        ValidationError: If parameters are invalid
    """
    if not isinstance(messages, list):
        raise ValidationError(
            "Invalid messages parameter",
            type=type(messages).__name__
        )
    
    log_message('INFO', 'storage', 'Finding image URLs via function',
               message_count=len(messages))
    return get_instance().find_image_urls(messages)