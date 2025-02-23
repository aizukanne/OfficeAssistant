import os
import pytest
from typing import Dict, Any
from unittest.mock import MagicMock

# Test configuration
TEST_CONFIG = {
    'api_keys': {
        'openai': 'test_openai_key',
        'google': 'test_google_key',
        'slack': 'test_slack_token',
        'openweather': 'test_weather_key'
    },
    'aws': {
        'region': 'us-east-1',
        'buckets': {
            'images': 'test-images-bucket',
            'documents': 'test-docs-bucket'
        },
        'tables': {
            'user': 'test_user_table',
            'assistant': 'test_assistant_table',
            'usernames': 'test_usernames_table',
            'channels': 'test_channels_table',
            'meetings': 'test_meetings_table'
        }
    },
    'nltk': {
        'data_path': '/tmp/nltk_data'
    }
}

@pytest.fixture
def mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up test environment variables."""
    for key, value in TEST_CONFIG['api_keys'].items():
        monkeypatch.setenv(f"{key.upper()}_API_KEY", value)

@pytest.fixture
def mock_aws() -> Dict[str, MagicMock]:
    """Mock AWS services."""
    mocks = {
        's3': MagicMock(),
        'dynamodb': MagicMock(),
        'dynamodb_table': MagicMock()
    }
    
    # Configure S3 mock
    mocks['s3'].put_object.return_value = {}
    mocks['s3'].get_object.return_value = {'Body': MagicMock()}
    mocks['s3'].list_objects_v2.return_value = {'Contents': []}
    
    # Configure DynamoDB mock
    mocks['dynamodb_table'].put_item.return_value = {}
    mocks['dynamodb_table'].get_item.return_value = {'Item': {}}
    mocks['dynamodb_table'].query.return_value = {'Items': []}
    mocks['dynamodb'].Table.return_value = mocks['dynamodb_table']
    
    return mocks

@pytest.fixture
def mock_requests() -> MagicMock:
    """Mock requests library."""
    mock = MagicMock()
    mock.get.return_value.json.return_value = {}
    mock.post.return_value.json.return_value = {}
    mock.put.return_value.json.return_value = {}
    mock.delete.return_value.json.return_value = {}
    return mock

@pytest.fixture
def mock_aiohttp() -> MagicMock:
    """Mock aiohttp client."""
    mock = MagicMock()
    mock.get.return_value.__aenter__.return_value.text.return_value = ""
    mock.get.return_value.__aenter__.return_value.read.return_value = b""
    return mock

@pytest.fixture
def mock_nltk() -> MagicMock:
    """Mock NLTK functionality."""
    mock = MagicMock()
    mock.word_tokenize.return_value = []
    mock.sent_tokenize.return_value = []
    return mock

@pytest.fixture
def sample_text() -> str:
    """Sample text for testing."""
    return """
    This is a sample text for testing purposes.
    It contains multiple sentences.
    Some sentences are short.
    Others are a bit longer and contain more words.
    """

@pytest.fixture
def sample_html() -> str:
    """Sample HTML for testing."""
    return """
    <html>
        <body>
            <h1>Sample Title</h1>
            <p>This is a paragraph.</p>
            <div>This is a div.</div>
        </body>
    </html>
    """

@pytest.fixture
def sample_json() -> Dict[str, Any]:
    """Sample JSON for testing."""
    return {
        "name": "Test",
        "value": 123,
        "nested": {
            "key": "value"
        },
        "array": [1, 2, 3]
    }

@pytest.fixture
def sample_message() -> Dict[str, Any]:
    """Sample message for testing."""
    return {
        "chat_id": "test_chat",
        "sort_key": 123456789,
        "message": "Test message",
        "role": "user",
        "thread": "test_thread",
        "image_urls": ["http://example.com/image.jpg"]
    }

@pytest.fixture
def sample_error() -> Dict[str, str]:
    """Sample error response for testing."""
    return {
        "status": "error",
        "code": "TEST_ERROR",
        "message": "Test error message",
        "details": None
    }