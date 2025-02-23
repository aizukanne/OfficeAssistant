import pytest
import boto3
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from src.services.storage_service import StorageService
from src.core.exceptions import (
    StorageError,
    DatabaseError,
    ValidationError
)

@pytest.fixture
def storage_service():
    """Create StorageService instance."""
    return StorageService()

@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table."""
    mock = MagicMock()
    mock.put_item.return_value = {}
    mock.get_item.return_value = {'Item': {'test': 'data'}}
    mock.query.return_value = {'Items': [{'test': 'data'}]}
    mock.scan.return_value = {'Items': [{'test': 'data'}]}
    mock.delete_item.return_value = {}
    return mock

@pytest.fixture
def mock_s3_client():
    """Mock S3 client."""
    mock = MagicMock()
    mock.put_object.return_value = {}
    mock.get_object.return_value = {'Body': MagicMock(read=lambda: b'test data')}
    mock.list_objects_v2.return_value = {'Contents': [{'Key': 'test.txt'}]}
    mock.delete_object.return_value = {}
    return mock

def test_initialization(storage_service):
    """Test service initialization."""
    assert storage_service.logger is not None
    assert storage_service.dynamodb is not None
    assert storage_service.s3_client is not None
    assert storage_service.tables is not None

def test_initialization_error():
    """Test initialization error handling."""
    with patch('boto3.resource', side_effect=Exception('Test error')):
        with pytest.raises(StorageError):
            StorageService()

def test_validate_config_missing_credentials(storage_service):
    """Test configuration validation with missing credentials."""
    with patch('boto3.Session') as mock_session:
        mock_session.return_value.get_credentials.return_value = None
        missing = storage_service.validate_config()
        assert 'AWS_CREDENTIALS' in missing

def test_validate_config_valid(storage_service):
    """Test configuration validation with valid credentials."""
    with patch('boto3.Session') as mock_session:
        mock_session.return_value.get_credentials.return_value = MagicMock()
        missing = storage_service.validate_config()
        assert not missing

def test_save_success(storage_service, mock_dynamodb_table):
    """Test successful data save."""
    storage_service.tables = {'test': mock_dynamodb_table}
    result = storage_service.save({'test': 'data'}, table='test')
    assert result is True
    mock_dynamodb_table.put_item.assert_called_once()

def test_save_missing_table(storage_service):
    """Test save with missing table parameter."""
    with pytest.raises(ValidationError):
        storage_service.save({'test': 'data'})

def test_save_database_error(storage_service, mock_dynamodb_table):
    """Test save with database error."""
    mock_dynamodb_table.put_item.side_effect = ClientError(
        {'Error': {'Code': 'TestError', 'Message': 'Test error'}},
        'PutItem'
    )
    storage_service.tables = {'test': mock_dynamodb_table}
    
    with pytest.raises(DatabaseError):
        storage_service.save({'test': 'data'}, table='test')

def test_retrieve_success(storage_service, mock_dynamodb_table):
    """Test successful data retrieval."""
    storage_service.tables = {'test': mock_dynamodb_table}
    result = storage_service.retrieve('test-id', table='test')
    assert result == {'test': 'data'}
    mock_dynamodb_table.get_item.assert_called_once()

def test_retrieve_missing_table(storage_service):
    """Test retrieve with missing table parameter."""
    with pytest.raises(ValidationError):
        storage_service.retrieve('test-id')

def test_retrieve_database_error(storage_service, mock_dynamodb_table):
    """Test retrieve with database error."""
    mock_dynamodb_table.get_item.side_effect = ClientError(
        {'Error': {'Code': 'TestError', 'Message': 'Test error'}},
        'GetItem'
    )
    storage_service.tables = {'test': mock_dynamodb_table}
    
    with pytest.raises(DatabaseError):
        storage_service.retrieve('test-id', table='test')

def test_delete_success(storage_service, mock_dynamodb_table):
    """Test successful data deletion."""
    storage_service.tables = {'test': mock_dynamodb_table}
    result = storage_service.delete('test-id', table='test')
    assert result is True
    mock_dynamodb_table.delete_item.assert_called_once()

def test_delete_missing_table(storage_service):
    """Test delete with missing table parameter."""
    with pytest.raises(ValidationError):
        storage_service.delete('test-id')

def test_delete_database_error(storage_service, mock_dynamodb_table):
    """Test delete with database error."""
    mock_dynamodb_table.delete_item.side_effect = ClientError(
        {'Error': {'Code': 'TestError', 'Message': 'Test error'}},
        'DeleteItem'
    )
    storage_service.tables = {'test': mock_dynamodb_table}
    
    with pytest.raises(DatabaseError):
        storage_service.delete('test-id', table='test')

def test_list_success(storage_service, mock_dynamodb_table):
    """Test successful data listing."""
    storage_service.tables = {'test': mock_dynamodb_table}
    result = storage_service.list(table='test')
    assert result == [{'test': 'data'}]
    mock_dynamodb_table.scan.assert_called_once()

def test_list_missing_table(storage_service):
    """Test list with missing table parameter."""
    with pytest.raises(ValidationError):
        storage_service.list()

def test_list_database_error(storage_service, mock_dynamodb_table):
    """Test list with database error."""
    mock_dynamodb_table.scan.side_effect = ClientError(
        {'Error': {'Code': 'TestError', 'Message': 'Test error'}},
        'Scan'
    )
    storage_service.tables = {'test': mock_dynamodb_table}
    
    with pytest.raises(DatabaseError):
        storage_service.list(table='test')

def test_save_message_success(storage_service):
    """Test successful message save."""
    with patch.object(storage_service, 'save') as mock_save:
        mock_save.return_value = True
        result = storage_service.save_message(
            'test-chat',
            'test message',
            'user',
            'test-thread',
            ['image1.jpg']
        )
        assert result is True
        mock_save.assert_called_once()

def test_get_last_messages_success(storage_service, mock_dynamodb_table):
    """Test successful last messages retrieval."""
    storage_service.tables = {'test': mock_dynamodb_table}
    result = storage_service.get_last_messages('test-chat', 5, 'test')
    assert result == [{'test': 'data'}]
    mock_dynamodb_table.query.assert_called_once()

def test_get_messages_in_range_success(storage_service, mock_dynamodb_table):
    """Test successful messages range retrieval."""
    storage_service.tables = {
        'user': mock_dynamodb_table,
        'assistant': mock_dynamodb_table
    }
    result = storage_service.get_messages_in_range('test-chat', 1, 10)
    assert len(result) == 2  # One from each table
    assert mock_dynamodb_table.query.call_count == 2

def test_upload_to_s3_success(storage_service, mock_s3_client):
    """Test successful S3 upload."""
    storage_service.s3_client = mock_s3_client
    result = storage_service.upload_to_s3(
        'images',
        b'test data',
        'test.jpg',
        'image/jpeg'
    )
    assert 'https://' in result
    mock_s3_client.put_object.assert_called_once()

def test_upload_to_s3_invalid_bucket(storage_service):
    """Test S3 upload with invalid bucket."""
    with pytest.raises(ValidationError):
        storage_service.upload_to_s3('invalid', b'test', 'test.jpg')

def test_upload_to_s3_error(storage_service, mock_s3_client):
    """Test S3 upload error."""
    mock_s3_client.put_object.side_effect = ClientError(
        {'Error': {'Code': 'TestError', 'Message': 'Test error'}},
        'PutObject'
    )
    storage_service.s3_client = mock_s3_client
    
    with pytest.raises(StorageError):
        storage_service.upload_to_s3('images', b'test', 'test.jpg')

def test_download_from_s3_success(storage_service, mock_s3_client):
    """Test successful S3 download."""
    storage_service.s3_client = mock_s3_client
    result = storage_service.download_from_s3('images', 'test.jpg')
    assert result == b'test data'
    mock_s3_client.get_object.assert_called_once()

def test_download_from_s3_invalid_bucket(storage_service):
    """Test S3 download with invalid bucket."""
    with pytest.raises(ValidationError):
        storage_service.download_from_s3('invalid', 'test.jpg')

def test_download_from_s3_error(storage_service, mock_s3_client):
    """Test S3 download error."""
    mock_s3_client.get_object.side_effect = ClientError(
        {'Error': {'Code': 'TestError', 'Message': 'Test error'}},
        'GetObject'
    )
    storage_service.s3_client = mock_s3_client
    
    with pytest.raises(StorageError):
        storage_service.download_from_s3('images', 'test.jpg')

def test_list_s3_files_success(storage_service, mock_s3_client):
    """Test successful S3 files listing."""
    storage_service.s3_client = mock_s3_client
    result = storage_service.list_s3_files('images')
    assert result == ['test.txt']
    mock_s3_client.list_objects_v2.assert_called_once()

def test_list_s3_files_with_prefix(storage_service, mock_s3_client):
    """Test S3 files listing with prefix."""
    storage_service.s3_client = mock_s3_client
    storage_service.list_s3_files('images', prefix='folder/')
    args = mock_s3_client.list_objects_v2.call_args[1]
    assert args['Prefix'] == 'folder/'

def test_find_image_urls(storage_service):
    """Test finding image URLs in messages."""
    messages = [
        {'image_urls': ['image1.jpg', 'image2.jpg']},
        {'text': 'No images'},
        {'image_urls': ['image3.jpg']}
    ]
    has_images, urls = storage_service.find_image_urls(messages)
    assert has_images is True
    assert len(urls) == 3
    assert 'image1.jpg' in urls
    assert 'image2.jpg' in urls
    assert 'image3.jpg' in urls