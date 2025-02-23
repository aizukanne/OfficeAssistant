from typing import Dict, Type, Any
from src.interfaces import ServiceInterface
from src.services.external_services import ExternalService
from src.services.storage_service import StorageService
from src.services.slack_service import SlackService
from src.services.openai_service import OpenAIService
from src.services.odoo_service import OdooService
from src.services.storage_functions import (
    save_message,
    get_last_messages,
    get_message_by_sort_id,
    get_messages_in_range,
    upload_to_s3,
    download_from_s3,
    delete_from_s3,
    list_s3_files,
    find_image_urls
)

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