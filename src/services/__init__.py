from typing import Dict, Type, Any

from src.services.interfaces import ServiceInterface
from src.services.external_services import ExternalService
from src.services.storage_service import StorageService
from src.services.slack_service import SlackService
from src.services.openai_service import OpenAIService
from src.services.odoo_service import OdooService

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
    'get_service'
]