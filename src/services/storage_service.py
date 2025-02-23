import json
import time
from typing import Dict, List, Tuple, Optional, Any
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Initialize S3 client
s3_client = boto3.client('s3')

# Connect to DynamoDB tables
user_table = dynamodb.Table('staff_history')
assistant_table = dynamodb.Table('maria_history')
names_table = dynamodb.Table('slack_usernames')
channels_table = dynamodb.Table('channels_table')
meetings_table = dynamodb.Table('meetings_table')

def save_message(
    table: Any,
    chat_id: str,
    text: str,
    role: str,
    thread: Optional[str] = None,
    image_urls: Optional[List[str]] = None
) -> None:
    """
    Saves a message to the specified DynamoDB table.
    
    Args:
        table: The DynamoDB table to save to
        chat_id: The chat ID
        text: The message text
        role: The role of the sender (user/assistant)
        thread: Optional thread timestamp
        image_urls: Optional list of image URLs
    """
    timestamp = int(time.time())
    sort_key = timestamp
    ttl = timestamp + 20 * 24 * 60 * 60  # 20 days TTL
    
    item = {
        'chat_id': chat_id,
        'sort_key': sort_key,
        'message': text,
        'role': role,
        'ttl': ttl
    }
    
    if thread is not None:
        item['thread'] = thread
    if image_urls is not None:
        item['image_urls'] = image_urls
        
    table.put_item(Item=item)

def get_last_messages(
    table: Any,
    chat_id: str,
    num_messages: int
) -> List[Dict]:
    """
    Retrieves the last N messages from a DynamoDB table.
    
    Args:
        table: The DynamoDB table to query
        chat_id: The chat ID
        num_messages: Number of messages to retrieve
        
    Returns:
        List[Dict]: List of retrieved messages
    """
    response = table.query(
        KeyConditionExpression=Key('chat_id').eq(chat_id),
        Limit=num_messages,
        ScanIndexForward=False
    )
    return response.get('Items', [])

def get_message_by_sort_id(
    role: str,
    chat_id: str,
    sort_id: int
) -> Optional[Dict]:
    """
    Retrieves a specific message by its sort ID.
    
    Args:
        role: The role to determine which table to query
        chat_id: The chat ID
        sort_id: The sort ID of the message
        
    Returns:
        Optional[Dict]: The message if found, None otherwise
    """
    table = user_table if role == 'user' else assistant_table
    response = table.query(
        KeyConditionExpression=Key('chat_id').eq(chat_id) & Key('sort_key').eq(sort_id),
        Limit=1
    )
    items = response.get('Items', [])
    return items[0] if items else None

def get_messages_in_range(
    chat_id: str,
    start_sort_id: int,
    end_sort_id: int
) -> List[Dict]:
    """
    Retrieves messages within a specified sort ID range.
    
    Args:
        chat_id: The chat ID
        start_sort_id: Starting sort ID
        end_sort_id: Ending sort ID
        
    Returns:
        List[Dict]: List of messages in the range
    """
    def query_table(table: Any) -> List[Dict]:
        return table.query(
            KeyConditionExpression=Key('chat_id').eq(chat_id) & 
                                 Key('sort_key').between(start_sort_id, end_sort_id)
        )['Items']

    user_messages = query_table(user_table)
    assistant_messages = query_table(assistant_table)
    
    all_messages = user_messages + assistant_messages
    all_messages.sort(key=lambda x: x['sort_key'])
    
    all_messages_summary = [summarize_messages(all_messages)]
    print(f"All Messages Summary: {json.dumps(all_messages_summary, default=decimal_default)}")
    
    return all_messages

def upload_to_s3(
    bucket_name: str,
    file_data: bytes,
    file_key: str,
    content_type: Optional[str] = None
) -> Optional[str]:
    """
    Uploads a file to an S3 bucket.
    
    Args:
        bucket_name: The name of the S3 bucket
        file_data: The file data to upload
        file_key: The key (path) for the file in S3
        content_type: Optional content type of the file
        
    Returns:
        Optional[str]: The URL of the uploaded file if successful, None otherwise
    """
    try:
        extra_args = {'ContentType': content_type} if content_type else {}
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_key,
            Body=file_data,
            **extra_args
        )
        return f"https://{bucket_name}.s3.amazonaws.com/{file_key}"
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        return None

def download_from_s3(
    bucket_name: str,
    file_key: str
) -> Optional[bytes]:
    """
    Downloads a file from an S3 bucket.
    
    Args:
        bucket_name: The name of the S3 bucket
        file_key: The key (path) of the file in S3
        
    Returns:
        Optional[bytes]: The file data if successful, None otherwise
    """
    try:
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=file_key
        )
        return response['Body'].read()
    except ClientError as e:
        print(f"Error downloading from S3: {e}")
        return None

def delete_from_s3(
    bucket_name: str,
    file_key: str
) -> bool:
    """
    Deletes a file from an S3 bucket.
    
    Args:
        bucket_name: The name of the S3 bucket
        file_key: The key (path) of the file to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        s3_client.delete_object(
            Bucket=bucket_name,
            Key=file_key
        )
        return True
    except ClientError as e:
        print(f"Error deleting from S3: {e}")
        return False

def list_s3_files(
    bucket_name: str,
    prefix: Optional[str] = None
) -> List[str]:
    """
    Lists files in an S3 bucket.
    
    Args:
        bucket_name: The name of the S3 bucket
        prefix: Optional prefix to filter files
        
    Returns:
        List[str]: List of file keys in the bucket
    """
    try:
        params = {'Bucket': bucket_name}
        if prefix:
            params['Prefix'] = prefix
            
        response = s3_client.list_objects_v2(**params)
        return [obj['Key'] for obj in response.get('Contents', [])]
    except ClientError as e:
        print(f"Error listing S3 files: {e}")
        return []

def find_image_urls(messages: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Finds image URLs in a list of messages.
    
    Args:
        messages: List of messages to search
        
    Returns:
        Tuple[bool, List[str]]: Tuple containing whether images were found and list of URLs
    """
    has_image_urls = False
    all_image_urls = []
    
    for message in messages:
        if 'image_urls' in message and message['image_urls']:
            has_image_urls = True
            all_image_urls.extend(message['image_urls'])
            
    return has_image_urls, all_image_urls

def decimal_default(obj: Any) -> Any:
    """
    JSON serializer for Decimal objects.
    
    Args:
        obj: Object to serialize
        
    Returns:
        Any: Serialized object
    """
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def list_files(folder_prefix: str = 'uploads') -> Dict[str, str]:
    """
    Lists the files in a specified folder in the S3 bucket.
    
    Args:
        folder_prefix: The prefix of the folder whose files to list (default: 'uploads')
        
    Returns:
        Dict[str, str]: Dictionary mapping file names to their S3 URLs
    """
    response = s3_client.list_objects_v2(Bucket=docs_bucket_name, Prefix=folder_prefix)

    files = {}
    if 'Contents' in response:
        for obj in response['Contents']:
            if not obj['Key'].endswith('/'):  # Exclude any subfolders
                file_url = f"https://{docs_bucket_name}.s3.amazonaws.com/{obj['Key']}"
                file_name = obj['Key'].split('/')[-1]  # Extract the file name from the key
                files[file_name] = file_url

    return files