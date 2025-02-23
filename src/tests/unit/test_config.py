import pytest
from unittest.mock import patch
from src.config.settings import (
    validate_config,
    get_proxy_url,
    get_user_agent,
    get_api_endpoint,
    get_table_name,
    get_bucket_name,
    PROXY_CONFIG,
    USER_AGENTS,
    API_ENDPOINTS,
    DYNAMODB_TABLES,
    S3_BUCKETS
)
from src.core.exceptions import ConfigurationError

def test_validate_config_with_missing_keys(mock_env):
    """Test configuration validation with missing required keys."""
    with patch.dict('os.environ', {}, clear=True):
        missing = validate_config()
        assert 'OPENAI_API_KEY' in missing
        assert 'GOOGLE_API_KEY' in missing
        assert 'GOOGLE_SEARCH_CX' in missing
        assert 'OPENWEATHER_KEY' in missing
        assert 'SLACK_BOT_TOKEN' in missing

def test_validate_config_with_all_keys(mock_env):
    """Test configuration validation with all required keys present."""
    with patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test_key',
        'GOOGLE_API_KEY': 'test_key',
        'GOOGLE_SEARCH_CX': 'test_cx',
        'OPENWEATHER_KEY': 'test_key',
        'SLACK_BOT_TOKEN': 'test_token'
    }):
        missing = validate_config()
        assert not missing

def test_get_proxy_url_enabled():
    """Test getting proxy URL when enabled."""
    with patch.dict(PROXY_CONFIG, {'enabled': True, 'url': 'test_proxy_url'}):
        assert get_proxy_url() == 'test_proxy_url'

def test_get_proxy_url_disabled():
    """Test getting proxy URL when disabled."""
    with patch.dict(PROXY_CONFIG, {'enabled': False, 'url': 'test_proxy_url'}):
        assert get_proxy_url() == ''

def test_get_user_agent():
    """Test getting random user agent."""
    agent = get_user_agent()
    assert agent in USER_AGENTS

def test_get_api_endpoint_valid():
    """Test getting valid API endpoint."""
    endpoint = get_api_endpoint('openweather', 'geo')
    assert endpoint == API_ENDPOINTS['openweather']['geo']

def test_get_api_endpoint_invalid_service():
    """Test getting API endpoint for invalid service."""
    endpoint = get_api_endpoint('invalid_service', 'endpoint')
    assert endpoint == ''

def test_get_api_endpoint_invalid_endpoint():
    """Test getting invalid API endpoint."""
    endpoint = get_api_endpoint('openweather', 'invalid_endpoint')
    assert endpoint == ''

def test_get_table_name_valid():
    """Test getting valid DynamoDB table name."""
    table_name = get_table_name('user')
    assert table_name == DYNAMODB_TABLES['user']

def test_get_table_name_invalid():
    """Test getting invalid DynamoDB table name."""
    table_name = get_table_name('invalid_table')
    assert table_name == ''

def test_get_bucket_name_valid():
    """Test getting valid S3 bucket name."""
    bucket_name = get_bucket_name('images')
    assert bucket_name == S3_BUCKETS['images']

def test_get_bucket_name_invalid():
    """Test getting invalid S3 bucket name."""
    bucket_name = get_bucket_name('invalid_bucket')
    assert bucket_name == ''

@pytest.mark.parametrize("service,endpoint,expected", [
    ('openweather', 'geo', 'http://api.openweathermap.org/geo/1.0/direct'),
    ('google', 'search', 'https://www.googleapis.com/customsearch/v1'),
    ('slack', 'message', 'https://slack.com/api/chat.postMessage'),
    ('invalid', 'invalid', ''),
])
def test_api_endpoints(service, endpoint, expected):
    """Test various API endpoints."""
    assert get_api_endpoint(service, endpoint) == expected

@pytest.mark.parametrize("table,expected", [
    ('user', 'staff_history'),
    ('assistant', 'maria_history'),
    ('usernames', 'slack_usernames'),
    ('invalid', ''),
])
def test_table_names(table, expected):
    """Test various table names."""
    assert get_table_name(table) == expected

@pytest.mark.parametrize("bucket,expected", [
    ('images', 'mariaimagefolder-us'),
    ('documents', 'mariadocsfolder-us'),
    ('invalid', ''),
])
def test_bucket_names(bucket, expected):
    """Test various bucket names."""
    assert get_bucket_name(bucket) == expected