import pytest
from unittest.mock import patch

from src.services import get_service
from src.services.interfaces import ServiceInterface
from src.services.external_services import ExternalService
from src.services.storage_service import StorageService
from src.services.slack_service import SlackService
from src.services.openai_service import OpenAIService
from src.services.odoo_service import OdooService

def test_get_external_service():
    """Test getting external service."""
    with patch('src.services.external_services.ExternalService') as mock_service:
        service = get_service('external')
        assert isinstance(service, ExternalService)
        mock_service.assert_called_once()

def test_get_storage_service():
    """Test getting storage service."""
    with patch('src.services.storage_service.StorageService') as mock_service:
        service = get_service('storage')
        assert isinstance(service, StorageService)
        mock_service.assert_called_once()

def test_get_slack_service():
    """Test getting slack service."""
    with patch('src.services.slack_service.SlackService') as mock_service:
        service = get_service('slack')
        assert isinstance(service, SlackService)
        mock_service.assert_called_once()

def test_get_openai_service():
    """Test getting OpenAI service."""
    with patch('src.services.openai_service.OpenAIService') as mock_service:
        service = get_service('openai')
        assert isinstance(service, OpenAIService)
        mock_service.assert_called_once()

def test_get_odoo_service():
    """Test getting Odoo service."""
    with patch('src.services.odoo_service.OdooService') as mock_service:
        service = get_service('odoo')
        assert isinstance(service, OdooService)
        mock_service.assert_called_once()

def test_get_service_with_params():
    """Test getting service with parameters."""
    params = {'param1': 'value1', 'param2': 'value2'}
    
    with patch('src.services.external_services.ExternalService') as mock_service:
        service = get_service('external', **params)
        mock_service.assert_called_once_with(**params)

def test_get_invalid_service():
    """Test getting invalid service type."""
    with pytest.raises(ValueError) as exc:
        get_service('invalid_service')
    assert 'Invalid service type: invalid_service' in str(exc.value)

def test_service_interface():
    """Test all services implement ServiceInterface."""
    services = [
        ExternalService,
        StorageService,
        SlackService,
        OpenAIService,
        OdooService
    ]
    
    for service_class in services:
        assert issubclass(service_class, ServiceInterface)

def test_service_required_methods():
    """Test all services implement required methods."""
    required_methods = [
        'initialize',
        'validate_config'
    ]
    
    services = [
        ExternalService,
        StorageService,
        SlackService,
        OpenAIService,
        OdooService
    ]
    
    for service_class in services:
        service_methods = dir(service_class)
        for method in required_methods:
            assert method in service_methods, f"{service_class.__name__} missing {method}"

@pytest.mark.parametrize("service_type,service_class", [
    ('external', ExternalService),
    ('storage', StorageService),
    ('slack', SlackService),
    ('openai', OpenAIService),
    ('odoo', OdooService)
])
def test_service_registry(service_type, service_class):
    """Test service registry mapping."""
    with patch(f'src.services.{service_type}_service.{service_class.__name__}') as mock_service:
        service = get_service(service_type)
        assert isinstance(service, service_class)
        mock_service.assert_called_once()

def test_service_initialization_error():
    """Test service initialization error handling."""
    with patch('src.services.external_services.ExternalService') as mock_service:
        mock_service.side_effect = Exception("Initialization error")
        with pytest.raises(Exception) as exc:
            get_service('external')
        assert "Initialization error" in str(exc.value)

def test_service_validation():
    """Test service configuration validation."""
    services = [
        ExternalService,
        StorageService,
        SlackService,
        OpenAIService,
        OdooService
    ]
    
    for service_class in services:
        with patch.object(service_class, 'validate_config') as mock_validate:
            mock_validate.return_value = {}
            service = service_class()
            mock_validate.assert_called_once()

def test_service_logger():
    """Test service logger initialization."""
    services = [
        ExternalService,
        StorageService,
        SlackService,
        OpenAIService,
        OdooService
    ]
    
    for service_class in services:
        service = service_class()
        assert hasattr(service, 'logger')
        assert service.logger is not None