import pytest
from unittest.mock import patch, MagicMock
import xmlrpc.client

from src.services.odoo_service import OdooService
from src.core.exceptions import (
    APIError,
    ValidationError,
    AuthenticationError,
    DatabaseError
)

@pytest.fixture
def odoo_service():
    """Create OdooService instance."""
    with patch.dict('os.environ', {
        'ODOO_URL': 'http://test.odoo.com',
        'ODOO_DB': 'test_db',
        'ODOO_USERNAME': 'admin',
        'ODOO_PASSWORD': 'admin'
    }):
        return OdooService()

@pytest.fixture
def mock_xmlrpc():
    """Mock XML-RPC client."""
    mock = MagicMock()
    
    # Mock common proxy
    mock.common = MagicMock()
    mock.common.authenticate.return_value = 1  # uid
    
    # Mock models proxy
    mock.models = MagicMock()
    mock.models.execute_kw.return_value = []
    
    return mock

def test_initialization(odoo_service):
    """Test service initialization."""
    assert odoo_service.logger is not None
    assert odoo_service.uid is not None
    assert odoo_service.db == 'test_db'

def test_initialization_error():
    """Test initialization error handling."""
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ValidationError):
            OdooService()

def test_validate_config_missing_values(odoo_service):
    """Test configuration validation with missing values."""
    with patch.dict('os.environ', {}, clear=True):
        missing = odoo_service.validate_config()
        assert 'ODOO_URL' in missing
        assert 'ODOO_DB' in missing
        assert 'ODOO_USERNAME' in missing
        assert 'ODOO_PASSWORD' in missing

def test_validate_config_valid(odoo_service):
    """Test configuration validation with valid values."""
    missing = odoo_service.validate_config()
    assert not missing

def test_get_models_success(odoo_service, mock_xmlrpc):
    """Test successful models retrieval."""
    odoo_service.models = mock_xmlrpc.models
    
    models = odoo_service.get_models()
    
    mock_xmlrpc.models.execute_kw.assert_called_once()
    assert isinstance(models, list)

def test_get_models_with_filter(odoo_service, mock_xmlrpc):
    """Test models retrieval with filter."""
    odoo_service.models = mock_xmlrpc.models
    
    odoo_service.get_models(name_like=['sale'])
    
    args = mock_xmlrpc.models.execute_kw.call_args[0]
    assert any('sale' in str(arg) for arg in args)

def test_get_models_error(odoo_service, mock_xmlrpc):
    """Test models retrieval error."""
    mock_xmlrpc.models.execute_kw.side_effect = xmlrpc.client.Fault(1, "Test error")
    odoo_service.models = mock_xmlrpc.models
    
    with pytest.raises(APIError):
        odoo_service.get_models()

def test_get_fields_success(odoo_service, mock_xmlrpc):
    """Test successful fields retrieval."""
    odoo_service.models = mock_xmlrpc.models
    mock_xmlrpc.models.execute_kw.return_value = {
        'name': {'type': 'char', 'string': 'Name', 'required': True}
    }
    
    fields = odoo_service.get_fields('res.partner')
    
    assert isinstance(fields, dict)
    assert 'name' in fields
    mock_xmlrpc.models.execute_kw.assert_called_once()

def test_get_fields_error(odoo_service, mock_xmlrpc):
    """Test fields retrieval error."""
    mock_xmlrpc.models.execute_kw.side_effect = xmlrpc.client.Fault(1, "Test error")
    odoo_service.models = mock_xmlrpc.models
    
    with pytest.raises(APIError):
        odoo_service.get_fields('res.partner')

def test_create_record_success(odoo_service, mock_xmlrpc):
    """Test successful record creation."""
    odoo_service.models = mock_xmlrpc.models
    mock_xmlrpc.models.execute_kw.return_value = [1]  # Record ID
    
    record_id = odoo_service.create_record(
        'res.partner',
        {'name': 'Test Partner'}
    )
    
    assert record_id == 1
    mock_xmlrpc.models.execute_kw.assert_called_once()

def test_create_multiple_records_success(odoo_service, mock_xmlrpc):
    """Test successful multiple records creation."""
    odoo_service.models = mock_xmlrpc.models
    mock_xmlrpc.models.execute_kw.return_value = [1, 2]  # Record IDs
    
    record_ids = odoo_service.create_record(
        'res.partner',
        [
            {'name': 'Partner 1'},
            {'name': 'Partner 2'}
        ]
    )
    
    assert record_ids == [1, 2]
    mock_xmlrpc.models.execute_kw.assert_called_once()

def test_create_record_error(odoo_service, mock_xmlrpc):
    """Test record creation error."""
    mock_xmlrpc.models.execute_kw.side_effect = xmlrpc.client.Fault(1, "Test error")
    odoo_service.models = mock_xmlrpc.models
    
    with pytest.raises(APIError):
        odoo_service.create_record('res.partner', {'name': 'Test'})

def test_fetch_records_success(odoo_service, mock_xmlrpc):
    """Test successful records fetch."""
    odoo_service.models = mock_xmlrpc.models
    mock_xmlrpc.models.execute_kw.return_value = [
        {'id': 1, 'name': 'Test'}
    ]
    
    records = odoo_service.fetch_records('res.partner')
    
    assert isinstance(records, list)
    assert len(records) == 1
    assert records[0]['name'] == 'Test'
    mock_xmlrpc.models.execute_kw.assert_called_once()

def test_fetch_records_with_criteria(odoo_service, mock_xmlrpc):
    """Test records fetch with criteria."""
    odoo_service.models = mock_xmlrpc.models
    
    odoo_service.fetch_records(
        'res.partner',
        criteria=[('is_company', '=', True)],
        limit=10
    )
    
    kwargs = mock_xmlrpc.models.execute_kw.call_args[1]
    assert 'limit' in kwargs
    assert kwargs['limit'] == 10

def test_fetch_records_error(odoo_service, mock_xmlrpc):
    """Test records fetch error."""
    mock_xmlrpc.models.execute_kw.side_effect = xmlrpc.client.Fault(1, "Test error")
    odoo_service.models = mock_xmlrpc.models
    
    with pytest.raises(APIError):
        odoo_service.fetch_records('res.partner')

def test_update_record_success(odoo_service, mock_xmlrpc):
    """Test successful record update."""
    odoo_service.models = mock_xmlrpc.models
    
    result = odoo_service.update_record(
        'res.partner',
        1,
        {'name': 'Updated Name'}
    )
    
    assert result is True
    mock_xmlrpc.models.execute_kw.assert_called_once()

def test_update_record_error(odoo_service, mock_xmlrpc):
    """Test record update error."""
    mock_xmlrpc.models.execute_kw.side_effect = xmlrpc.client.Fault(1, "Test error")
    odoo_service.models = mock_xmlrpc.models
    
    with pytest.raises(APIError):
        odoo_service.update_record('res.partner', 1, {'name': 'Test'})

def test_delete_records_success(odoo_service, mock_xmlrpc):
    """Test successful records deletion."""
    odoo_service.models = mock_xmlrpc.models
    mock_xmlrpc.models.execute_kw.side_effect = [
        [1, 2],  # search result
        True     # unlink result
    ]
    
    result = odoo_service.delete_records(
        'res.partner',
        [('id', 'in', [1, 2])]
    )
    
    assert result is True
    assert mock_xmlrpc.models.execute_kw.call_count == 2

def test_delete_records_error(odoo_service, mock_xmlrpc):
    """Test records deletion error."""
    mock_xmlrpc.models.execute_kw.side_effect = xmlrpc.client.Fault(1, "Test error")
    odoo_service.models = mock_xmlrpc.models
    
    with pytest.raises(APIError):
        odoo_service.delete_records('res.partner', [])

def test_print_record_success(odoo_service, mock_xmlrpc):
    """Test successful record printing."""
    odoo_service.models = mock_xmlrpc.models
    mock_xmlrpc.models.execute_kw.return_value = b'PDF content'
    
    result = odoo_service.print_record('sale.order', 1)
    
    assert result == b'PDF content'
    mock_xmlrpc.models.execute_kw.assert_called_once()

def test_print_record_no_content(odoo_service, mock_xmlrpc):
    """Test record printing with no content."""
    mock_xmlrpc.models.execute_kw.return_value = None
    odoo_service.models = mock_xmlrpc.models
    
    with pytest.raises(APIError):
        odoo_service.print_record('sale.order', 1)

def test_execute_workflow_success(odoo_service, mock_xmlrpc):
    """Test successful workflow execution."""
    odoo_service.models = mock_xmlrpc.models
    
    result = odoo_service.execute_workflow(
        'sale.order',
        1,
        'order_confirm'
    )
    
    assert result is True
    mock_xmlrpc.models.exec_workflow.assert_called_once()

def test_execute_workflow_error(odoo_service, mock_xmlrpc):
    """Test workflow execution error."""
    mock_xmlrpc.models.exec_workflow.side_effect = xmlrpc.client.Fault(1, "Test error")
    odoo_service.models = mock_xmlrpc.models
    
    with pytest.raises(APIError):
        odoo_service.execute_workflow('sale.order', 1, 'order_confirm')