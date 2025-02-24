"""Type stubs for storage service."""
from typing import Dict, List, Optional, Any, Tuple
from mypy_boto3_s3.client import S3Client
from mypy_boto3_dynamodb.service_resource import (
    DynamoDBServiceResource,
    Table
)
from src.interfaces import StorageServiceInterface

class StorageService(StorageServiceInterface):
    """Storage service type hints."""
    
    s3_client: S3Client
    dynamodb: DynamoDBServiceResource
    tables: Dict[str, Table]
    
    def __init__(self) -> None: ...
    
    def initialize(self) -> None: ...
    
    def validate_config(self) -> Dict[str, str]: ...
    
    def save(
        self,
        data: Dict[str, Any],
        **kwargs: Any
    ) -> bool: ...
    
    def retrieve(
        self,
        identifier: str,
        **kwargs: Any
    ) -> Optional[Dict[str, Any]]: ...
    
    def delete(
        self,
        identifier: str,
        **kwargs: Any
    ) -> bool: ...
    
    def list(
        self,
        **kwargs: Any
    ) -> List[Dict[str, Any]]: ...
    
    def save_message(
        self,
        chat_id: str,
        text: str,
        role: str,
        thread: Optional[str] = None,
        image_urls: Optional[List[str]] = None
    ) -> bool: ...
    
    def get_last_messages(
        self,
        chat_id: str,
        num_messages: int,
        table: str
    ) -> List[Dict]: ...
    
    def get_messages_in_range(
        self,
        chat_id: str,
        start_sort_id: int,
        end_sort_id: int
    ) -> List[Dict]: ...
    
    def upload_to_s3(
        self,
        bucket: str,
        file_data: bytes,
        file_key: str,
        content_type: Optional[str] = None
    ) -> str: ...
    
    def download_from_s3(
        self,
        bucket: str,
        file_key: str
    ) -> bytes: ...
    
    def delete_from_s3(
        self,
        bucket: str,
        file_key: str
    ) -> bool: ...
    
    def list_s3_files(
        self,
        bucket: str,
        prefix: Optional[str] = None
    ) -> List[str]: ...
    
    def find_image_urls(
        self,
        messages: List[Dict]
    ) -> Tuple[bool, List[str]]: ...