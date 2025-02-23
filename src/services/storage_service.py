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
    ConfigurationError
)
from src.core.logging import ServiceLogger, log_function_call, log_error
from src.interfaces import StorageServiceInterface

# Initialize logger at module level
logger = ServiceLogger('storage_services')

# Create singleton instance
_instance = None

def get_instance():
    """Get singleton instance."""
    global _instance
    if _instance is None:
        _instance = StorageService()
    return _instance

class StorageService(StorageServiceInterface):
    """Implementation of storage service interface."""
    
    def __init__(self):
        """Initialize the service."""
        self.logger = ServiceLogger('storage_services')
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
        except Exception as e:
            self.logger.critical("Failed to initialize AWS clients", error=str(e))
            raise StorageError("Failed to initialize AWS clients")
    
    def validate_config(self) -> Dict[str, str]:
        """Validate service configuration."""
        missing = {}
        
        # Check AWS credentials
        if not boto3.Session().get_credentials():
            missing['AWS_CREDENTIALS'] = "AWS credentials are required"
            
        return missing

    @log_function_call(logger)
    @log_error(logger)
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
            return True
        except ClientError as e:
            self.logger.error("Failed to save data", error=str(e))
            raise DatabaseError("Failed to save data")

    @log_function_call(logger)
    @log_error(logger)
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
            return response.get('Item')
        except ClientError as e:
            self.logger.error("Failed to retrieve data", error=str(e))
            raise DatabaseError("Failed to retrieve data")

    @log_function_call(logger)
    @log_error(logger)
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
            return True
        except ClientError as e:
            self.logger.error("Failed to delete data", error=str(e))
            raise DatabaseError("Failed to delete data")

    @log_function_call(logger)
    @log_error(logger)
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
            return response.get('Items', [])
        except ClientError as e:
            self.logger.error("Failed to list data", error=str(e))
            raise DatabaseError("Failed to list data")

    @log_function_call(logger)
    @log_error(logger)
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
            
        return self.save(item, table='user' if role == 'user' else 'assistant')

    @log_function_call(logger)
    @log_error(logger)
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
            return response.get('Items', [])
        except ClientError as e:
            self.logger.error("Failed to get messages", error=str(e))
            raise DatabaseError("Failed to get messages")

    @log_function_call(logger)
    @log_error(logger)
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
                self.logger.error(f"Failed to query table {table}", error=str(e))
                raise DatabaseError(f"Failed to query table {table}")

        user_messages = query_table('user')
        assistant_messages = query_table('assistant')
        
        all_messages = user_messages + assistant_messages
        all_messages.sort(key=lambda x: x['sort_key'])
        
        return all_messages

    @log_function_call(logger)
    @log_error(logger)
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
            return f"https://{bucket_name}.s3.amazonaws.com/{file_key}"
        except ClientError as e:
            self.logger.error("Failed to upload to S3", error=str(e))
            raise StorageError("Failed to upload to S3")

    @log_function_call(logger)
    @log_error(logger)
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
            return response['Body'].read()
        except ClientError as e:
            self.logger.error("Failed to download from S3", error=str(e))
            raise StorageError("Failed to download from S3")

    @log_function_call(logger)
    @log_error(logger)
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
            return True
        except ClientError as e:
            self.logger.error("Failed to delete from S3", error=str(e))
            raise StorageError("Failed to delete from S3")

    @log_function_call(logger)
    @log_error(logger)
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
            return [obj['Key'] for obj in response.get('Contents', [])]
        except ClientError as e:
            self.logger.error("Failed to list S3 files", error=str(e))
            raise StorageError("Failed to list S3 files")

    def find_image_urls(self, messages: List[Dict]) -> Tuple[bool, List[str]]:
        """Find image URLs in messages."""
        image_urls = []
        for message in messages:
            if 'image_urls' in message and message['image_urls']:
                image_urls.extend(message['image_urls'])
                
        return bool(image_urls), image_urls