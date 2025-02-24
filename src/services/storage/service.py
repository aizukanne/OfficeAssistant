"""Storage service implementation."""
import json
import time
import boto3
from typing import Dict, List, Tuple, Optional, Any
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from decimal import Decimal

from src.config.settings import (
    get_table_name,
    get_bucket_name,
    DYNAMODB_TABLES
)
from src.core.exceptions import (
    StorageError,
    DatabaseError,
    ValidationError,
    ConfigurationError,
    S3Error,
    DynamoDBError
)
from src.interfaces import StorageServiceInterface
from src.utils.logging import log_message, log_error
from src.utils.decorators import log_function_call, log_error_decorator
from src.utils.error_handling import (
    handle_service_error,
    with_error_recovery,
    retry_with_backoff,
    wrap_exceptions
)

# Singleton instance
_instance = None

def get_instance() -> 'StorageService':
    """Get singleton instance."""
    global _instance
    if _instance is None:
        _instance = StorageService()
    return _instance

class StorageService(StorageServiceInterface):
    """Implementation of storage service interface."""
    
    def __init__(self) -> None:
        """Initialize the service."""
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize AWS clients and resources."""
        try:
            self.dynamodb = boto3.resource('dynamodb')
            self.s3_client = boto3.client('s3')
            
            # Initialize DynamoDB tables
            self.tables = {
                name: self.dynamodb.Table(table_name)
                for name, table_name in DYNAMODB_TABLES.items()
            }
            log_message('INFO', 'storage', 'Service initialized',
                       tables=list(self.tables.keys()))
        except Exception as e:
            handle_service_error(
                'storage',
                'initialize',
                ConfigurationError,
                tables=list(DYNAMODB_TABLES.keys())
            )(e)
    
    def validate_config(self) -> Dict[str, str]:
        """Validate service configuration."""
        missing = {}
        
        # Check AWS credentials
        if not boto3.Session().get_credentials():
            missing['AWS_CREDENTIALS'] = "AWS credentials are required"
            log_message('ERROR', 'storage', 'Missing AWS credentials')
            
        return missing

    @log_function_call('storage')
    @wrap_exceptions(StorageError, operation='save')
    def save(
        self,
        data: Dict[str, Any],
        **kwargs: Any
    ) -> bool:
        """Save data to storage."""
        table = kwargs.get('table')
        if not table:
            raise ValidationError("Table name is required")
            
        try:
            self.tables[table].put_item(Item=data)
            log_message('INFO', 'storage', 'Data saved',
                       table=table, data_id=data.get('id'))
            return True
        except ClientError as e:
            handle_service_error(
                'storage',
                'save',
                DynamoDBError,
                table=table,
                data_id=data.get('id')
            )(e)

    @log_function_call('storage')
    @wrap_exceptions(StorageError, operation='retrieve')
    def retrieve(
        self,
        identifier: str,
        **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        """Retrieve data from storage."""
        table = kwargs.get('table')
        if not table:
            raise ValidationError("Table name is required")
            
        try:
            response = self.tables[table].get_item(
                Key={'chat_id': identifier}
            )
            log_message('INFO', 'storage', 'Data retrieved',
                       table=table, identifier=identifier)
            return response.get('Item')
        except ClientError as e:
            handle_service_error(
                'storage',
                'retrieve',
                DynamoDBError,
                table=table,
                identifier=identifier
            )(e)

    @log_function_call('storage')
    @wrap_exceptions(StorageError, operation='delete')
    def delete(
        self,
        identifier: str,
        **kwargs: Any
    ) -> bool:
        """Delete data from storage."""
        table = kwargs.get('table')
        if not table:
            raise ValidationError("Table name is required")
            
        try:
            self.tables[table].delete_item(
                Key={'chat_id': identifier}
            )
            log_message('INFO', 'storage', 'Data deleted',
                       table=table, identifier=identifier)
            return True
        except ClientError as e:
            handle_service_error(
                'storage',
                'delete',
                DynamoDBError,
                table=table,
                identifier=identifier
            )(e)

    @log_function_call('storage')
    @wrap_exceptions(StorageError, operation='list')
    def list(
        self,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """List stored data."""
        table = kwargs.get('table')
        if not table:
            raise ValidationError("Table name is required")
            
        try:
            response = self.tables[table].scan()
            items = response.get('Items', [])
            log_message('INFO', 'storage', 'Data listed',
                       table=table, count=len(items))
            return items
        except ClientError as e:
            handle_service_error(
                'storage',
                'list',
                DynamoDBError,
                table=table
            )(e)

    @log_function_call('storage')
    @wrap_exceptions(StorageError, operation='save_message')
    def save_message(
        self,
        chat_id: str,
        text: str,
        role: str,
        thread: Optional[str] = None,
        image_urls: Optional[List[str]] = None
    ) -> bool:
        """Save a message to DynamoDB."""
        timestamp = int(time.time())
        ttl = timestamp + 20 * 24 * 60 * 60  # 20 days TTL
        
        item = {
            'chat_id': chat_id,
            'sort_key': timestamp,
            'message': text,
            'role': role,
            'ttl': ttl
        }
        
        if thread is not None:
            item['thread'] = thread
        if image_urls is not None:
            item['image_urls'] = image_urls
            
        log_message('INFO', 'storage', 'Saving message',
                   chat_id=chat_id, role=role)
        return self.save(item, table='user' if role == 'user' else 'assistant')

    @log_function_call('storage')
    @wrap_exceptions(StorageError, operation='get_last_messages')
    def get_last_messages(
        self,
        chat_id: str,
        num_messages: int,
        table: str
    ) -> List[Dict]:
        """Retrieve the last N messages from DynamoDB."""
        try:
            response = self.tables[table].query(
                KeyConditionExpression=Key('chat_id').eq(chat_id),
                Limit=num_messages,
                ScanIndexForward=False
            )
            messages = response.get('Items', [])
            log_message('INFO', 'storage', 'Retrieved messages',
                       chat_id=chat_id, count=len(messages))
            return messages
        except ClientError as e:
            handle_service_error(
                'storage',
                'get_last_messages',
                DynamoDBError,
                chat_id=chat_id,
                table=table
            )(e)

    @log_function_call('storage')
    @wrap_exceptions(StorageError, operation='get_messages_in_range')
    def get_messages_in_range(
        self,
        chat_id: str,
        start_sort_id: int,
        end_sort_id: int
    ) -> List[Dict]:
        """Retrieve messages within a sort ID range."""
        def query_table(table: str) -> List[Dict]:
            try:
                response = self.tables[table].query(
                    KeyConditionExpression=Key('chat_id').eq(chat_id) & 
                                         Key('sort_key').between(start_sort_id, end_sort_id)
                )
                return response.get('Items', [])
            except ClientError as e:
                handle_service_error(
                    'storage',
                    'query_table',
                    DynamoDBError,
                    chat_id=chat_id,
                    table=table
                )(e)

        user_messages = query_table('user')
        assistant_messages = query_table('assistant')
        
        all_messages = user_messages + assistant_messages
        all_messages.sort(key=lambda x: x['sort_key'])
        
        log_message('INFO', 'storage', 'Retrieved messages in range',
                   chat_id=chat_id, count=len(all_messages))
        return all_messages

    @log_function_call('storage')
    @retry_with_backoff(max_retries=3, exceptions=(ClientError,))
    @wrap_exceptions(StorageError, operation='upload_to_s3')
    def upload_to_s3(
        self,
        bucket: str,
        file_data: bytes,
        file_key: str,
        content_type: Optional[str] = None
    ) -> str:
        """Upload a file to S3."""
        bucket_name = get_bucket_name(bucket)
        if not bucket_name:
            raise ValidationError(f"Invalid bucket identifier: {bucket}")

        try:
            extra_args = {'ContentType': content_type} if content_type else {}
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=file_key,
                Body=file_data,
                **extra_args
            )
            url = f"https://{bucket_name}.s3.amazonaws.com/{file_key}"
            log_message('INFO', 'storage', 'File uploaded to S3',
                       bucket=bucket_name, key=file_key)
            return url
        except ClientError as e:
            handle_service_error(
                'storage',
                'upload_to_s3',
                S3Error,
                bucket=bucket_name,
                key=file_key
            )(e)

    @log_function_call('storage')
    @retry_with_backoff(max_retries=3, exceptions=(ClientError,))
    @wrap_exceptions(StorageError, operation='download_from_s3')
    def download_from_s3(
        self,
        bucket: str,
        file_key: str
    ) -> bytes:
        """Download a file from S3."""
        bucket_name = get_bucket_name(bucket)
        if not bucket_name:
            raise ValidationError(f"Invalid bucket identifier: {bucket}")

        try:
            response = self.s3_client.get_object(
                Bucket=bucket_name,
                Key=file_key
            )
            log_message('INFO', 'storage', 'File downloaded from S3',
                       bucket=bucket_name, key=file_key)
            return response['Body'].read()
        except ClientError as e:
            handle_service_error(
                'storage',
                'download_from_s3',
                S3Error,
                bucket=bucket_name,
                key=file_key
            )(e)

    @log_function_call('storage')
    @retry_with_backoff(max_retries=3, exceptions=(ClientError,))
    @wrap_exceptions(StorageError, operation='delete_from_s3')
    def delete_from_s3(
        self,
        bucket: str,
        file_key: str
    ) -> bool:
        """Delete a file from S3."""
        bucket_name = get_bucket_name(bucket)
        if not bucket_name:
            raise ValidationError(f"Invalid bucket identifier: {bucket}")

        try:
            self.s3_client.delete_object(
                Bucket=bucket_name,
                Key=file_key
            )
            log_message('INFO', 'storage', 'File deleted from S3',
                       bucket=bucket_name, key=file_key)
            return True
        except ClientError as e:
            handle_service_error(
                'storage',
                'delete_from_s3',
                S3Error,
                bucket=bucket_name,
                key=file_key
            )(e)

    @log_function_call('storage')
    @retry_with_backoff(max_retries=3, exceptions=(ClientError,))
    @wrap_exceptions(StorageError, operation='list_s3_files')
    def list_s3_files(
        self,
        bucket: str,
        prefix: Optional[str] = None
    ) -> List[str]:
        """List files in an S3 bucket."""
        bucket_name = get_bucket_name(bucket)
        if not bucket_name:
            raise ValidationError(f"Invalid bucket identifier: {bucket}")

        try:
            params = {'Bucket': bucket_name}
            if prefix:
                params['Prefix'] = prefix
                
            response = self.s3_client.list_objects_v2(**params)
            files = [obj['Key'] for obj in response.get('Contents', [])]
            log_message('INFO', 'storage', 'Listed S3 files',
                       bucket=bucket_name, count=len(files))
            return files
        except ClientError as e:
            handle_service_error(
                'storage',
                'list_s3_files',
                S3Error,
                bucket=bucket_name
            )(e)

    def find_image_urls(self, messages: List[Dict]) -> Tuple[bool, List[str]]:
        """Find image URLs in messages."""
        image_urls = []
        for message in messages:
            if 'image_urls' in message and message['image_urls']:
                image_urls.extend(message['image_urls'])
                
        has_images = bool(image_urls)
        log_message('INFO', 'storage', 'Found image URLs',
                   has_images=has_images, count=len(image_urls))
        return has_images, image_urls