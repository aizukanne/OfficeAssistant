from typing import Dict, Type, Any, List, Optional, Tuple, Union
from src.services.interfaces import ServiceInterface
from src.services.external_services import ExternalService
from src.services.storage_service import StorageService
from src.services.slack_service import SlackService
from src.services.openai_service import OpenAIService
from src.services.odoo_service import OdooService

# Create singleton instances
_storage_service = StorageService()

# Map of service types to their implementations
SERVICE_REGISTRY: Dict[str, Type[ServiceInterface]] = {
    'external': ExternalService,
    'storage': StorageService,
    'slack': SlackService,
    'openai': OpenAIService,
    'odoo': OdooService
}

def get_service(service_type: str, **kwargs: Any) -> ServiceInterface:
    """Get a service instance."""
    if service_type not in SERVICE_REGISTRY:
        raise ValueError(f"Invalid service type: {service_type}")
    service_class = SERVICE_REGISTRY[service_type]
    return service_class(**kwargs)

# Export storage service methods
def save_message(chat_id: str, text: str, role: str, thread: Optional[str] = None, image_urls: Optional[List[str]] = None) -> bool:
    return _storage_service.save_message(chat_id, text, role, thread, image_urls)

def get_last_messages(chat_id: str, num_messages: int, table: str) -> List[Dict]:
    return _storage_service.get_last_messages(chat_id, num_messages, table)

def get_message_by_sort_id(chat_id: str, sort_id: int, table: str) -> Optional[Dict]:
    return _storage_service.get_message_by_sort_id(chat_id, sort_id, table)

def get_messages_in_range(chat_id: str, start_sort_id: int, end_sort_id: int) -> List[Dict]:
    return _storage_service.get_messages_in_range(chat_id, start_sort_id, end_sort_id)

def upload_to_s3(bucket: str, file_data: bytes, file_key: str, content_type: Optional[str] = None) -> str:
    return _storage_service.upload_to_s3(bucket, file_data, file_key, content_type)

def download_from_s3(bucket: str, file_key: str) -> bytes:
    return _storage_service.download_from_s3(bucket, file_key)

def delete_from_s3(bucket: str, file_key: str) -> bool:
    return _storage_service.delete_from_s3(bucket, file_key)

def list_s3_files(bucket: str, prefix: Optional[str] = None) -> List[str]:
    return _storage_service.list_s3_files(bucket, prefix)

def find_image_urls(messages: List[Dict]) -> Tuple[bool, List[str]]:
    return _storage_service.find_image_urls(messages)

__all__ = [
    'ServiceInterface',
    'ExternalService',
    'StorageService',
    'SlackService',
    'OpenAIService',
    'OdooService',
    'get_service',
    
    # Storage Service Methods
    'save_message',
    'get_last_messages',
    'get_message_by_sort_id',
    'get_messages_in_range',
    'upload_to_s3',
    'download_from_s3',
    'delete_from_s3',
    'list_s3_files',
    'find_image_urls'
]