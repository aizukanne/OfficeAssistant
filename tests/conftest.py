"""Standard test fixtures."""
import os
import pytest
from typing import Dict, Any
from unittest.mock import MagicMock
import boto3
import requests

from src.services.storage import StorageService
from src.services.slack import SlackService
from src.services.openai import OpenAIService
from src.services.odoo import OdooService
from src.services.external import ExternalService

from .utils.test_utils import (
    create_aws_mock,
    create_http_mock,
    create_service_mock,
    create_response_mock
)

# AWS Fixtures
@pytest.fixture
def mock_s3() -> MagicMock:
    """Create mock S3 client."""
    mock = MagicMock()
    mock.upload_fileobj.return_value = None
    mock.download_fileobj.return_value = None
    mock.delete_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
    return mock

@pytest.fixture
def mock_dynamodb() -> MagicMock:
    """Create mock DynamoDB resource."""
    mock = MagicMock()
    table_mock = MagicMock()
    table_mock.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
    table_mock.get_item.return_value = {'Item': {'id': 'test'}}
    table_mock.delete_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
    mock.Table.return_value = table_mock
    return mock

@pytest.fixture
def mock_aws_services(mock_s3: MagicMock, mock_dynamodb: MagicMock) -> Dict[str, MagicMock]:
    """Create mock AWS services."""
    return {
        's3': mock_s3,
        'dynamodb': mock_dynamodb
    }

# Service Fixtures
@pytest.fixture
def mock_storage_service(mock_aws_services: Dict[str, MagicMock]) -> MagicMock:
    """Create mock storage service."""
    service = create_service_mock(StorageService)
    service.s3_client = mock_aws_services['s3']
    service.dynamodb = mock_aws_services['dynamodb']
    return service

@pytest.fixture
def mock_slack_service() -> MagicMock:
    """Create mock Slack service."""
    return create_service_mock(
        SlackService,
        send_message=True,
        send_file=True
    )

@pytest.fixture
def mock_openai_service() -> MagicMock:
    """Create mock OpenAI service."""
    return create_service_mock(
        OpenAIService,
        generate_content="Generated content",
        get_embedding=[0.1, 0.2, 0.3]
    )

@pytest.fixture
def mock_odoo_service() -> MagicMock:
    """Create mock Odoo service."""
    return create_service_mock(
        OdooService,
        create_record=1,
        update_record=True
    )

@pytest.fixture
def mock_external_service() -> MagicMock:
    """Create mock external service."""
    return create_service_mock(
        ExternalService,
        search=[{'title': 'Result', 'url': 'http://example.com'}]
    )

# HTTP Client Fixtures
@pytest.fixture
def mock_http_client() -> MagicMock:
    """Create mock HTTP client."""
    return create_http_mock(
        responses={
            '/api/test': {'data': 'test'},
            '/api/error': {'error': 'test error'}
        },
        status_codes={
            '/api/test': 200,
            '/api/error': 400
        }
    )

@pytest.fixture
def mock_session(mock_http_client: MagicMock) -> MagicMock:
    """Create mock requests session."""
    session = MagicMock(spec=requests.Session)
    session.get.side_effect = mock_http_client.request
    session.post.side_effect = mock_http_client.request
    return session

# Test Data Fixtures
@pytest.fixture
def test_data() -> Dict[str, Any]:
    """Provide test data."""
    return {
        'id': 'test-123',
        'content': 'test content',
        'metadata': {
            'type': 'test',
            'created_at': '2025-02-24T01:54:00Z'
        }
    }

@pytest.fixture
def test_file(tmp_path: str) -> str:
    """Create test file."""
    file_path = os.path.join(tmp_path, 'test.txt')
    with open(file_path, 'w') as f:
        f.write('test content')
    return file_path

@pytest.fixture
def test_image(tmp_path: str) -> bytes:
    """Create test image data."""
    return b'fake image data'

# Environment Fixtures
@pytest.fixture
def mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up test environment variables."""
    env_vars = {
        'AWS_ACCESS_KEY_ID': 'test-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret',
        'SLACK_BOT_TOKEN': 'test-token',
        'OPENAI_API_KEY': 'test-key',
        'ODOO_URL': 'http://test.odoo.com',
        'ODOO_DB': 'test-db',
        'ODOO_USERNAME': 'test-user',
        'ODOO_PASSWORD': 'test-pass'
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

# Error Fixtures
@pytest.fixture
def mock_error_response() -> MagicMock:
    """Create mock error response."""
    return create_response_mock(
        {'error': 'test error'},
        status_code=400,
        headers={'Content-Type': 'application/json'}
    )

@pytest.fixture
def mock_timeout_response() -> MagicMock:
    """Create mock timeout response."""
    mock = MagicMock()
    mock.side_effect = requests.exceptions.Timeout("Request timed out")
    return mock

# Cleanup Fixtures
@pytest.fixture(autouse=True)
def cleanup_mocks() -> None:
    """Clean up mocks after each test."""
    yield
    # Reset any global state here if needed