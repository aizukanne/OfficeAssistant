"""Services package."""
from typing import Dict, Type, Any
from src.interfaces import ServiceInterface

# Import services from their new locations
from .storage import (
    StorageService,
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
from .slack import SlackService
from .openai import OpenAIService
from .odoo import OdooService
from .external import ExternalService

# Map of service types to their implementations
SERVICE_REGISTRY: Dict[str, Type[ServiceInterface]] = {
    'external': ExternalService,
    'storage': StorageService,
    'slack': SlackService,
    'openai': OpenAIService,
    'odoo': OdooService
}

def get_service(service_type: str, **kwargs: Any) -> ServiceInterface:
    """
    Get a service instance.
    
    Args:
        service_type: Type of service to get
        **kwargs: Additional parameters for service initialization
        
    Returns:
        ServiceInterface: Service instance
        
    Raises:
        ValueError: If service type is invalid
    """
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