import pytest
from unittest.mock import patch, MagicMock
from slack_sdk.errors import SlackApiError

from src.services.slack_service import SlackService
from src.core.exceptions import (
    APIError,
    ValidationError,
    AuthenticationError
)

@pytest.fixture
def slack_service():
    """Create SlackService instance."""
    return SlackService()

@pytest.fixture
def mock_slack_client():
    """Mock Slack client."""
    mock = MagicMock()
    mock.chat_postMessage.return_value = {'ok': True}
    mock.files_upload_v2.return_value = {'ok': True}
    mock.users_info.return_value = {'user': {'id': 'U123', 'name': 'test'}}
    mock.users_list.return_value = {'members': [{'id': 'U123', 'name': 'test'}]}
    mock.conversations_info.return_value = {'channel': {'id': 'C123', 'name': 'test'}}
    mock.conversations_list.return_value = {'channels': [{'id': 'C123', 'name': 'test'}]}
    mock.search_messages.return_value = {'messages': {'matches': []}}
    return mock

def test_initialization(slack_service):
    """Test service initialization."""
    assert slack_service.logger is not None
    assert slack_service.storage is not None

def test_initialization_error():
    """Test initialization error handling."""
    with patch('slack_sdk.WebClient', side_effect=Exception('Test error')):
        with pytest.raises(AuthenticationError):
            SlackService()

def test_validate_config_missing_token(slack_service):
    """Test configuration validation with missing token."""
    with patch.dict('os.environ', {}, clear=True):
        missing = slack_service.validate_config()
        assert 'SLACK_BOT_TOKEN' in missing

def test_validate_config_valid(slack_service):
    """Test configuration validation with valid token."""
    with patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'test_token'}):
        missing = slack_service.validate_config()
        assert not missing

def test_send_message_success(slack_service, mock_slack_client):
    """Test successful message sending."""
    slack_service.client = mock_slack_client
    
    result = slack_service.send_message(
        message="test message",
        recipient="C123"
    )
    
    assert result is True
    mock_slack_client.chat_postMessage.assert_called_once()

def test_send_message_empty(slack_service):
    """Test sending empty message."""
    with pytest.raises(ValidationError):
        slack_service.send_message("", "C123")

def test_send_message_api_error(slack_service, mock_slack_client):
    """Test message sending API error."""
    mock_slack_client.chat_postMessage.side_effect = SlackApiError(
        "Error", {"error": "test error"}
    )
    slack_service.client = mock_slack_client
    
    with pytest.raises(APIError):
        slack_service.send_message("test", "C123")

def test_send_file_success(slack_service, mock_slack_client):
    """Test successful file sending."""
    slack_service.client = mock_slack_client
    
    result = slack_service.send_file(
        file_path="test.txt",
        recipient="C123",
        title="Test File"
    )
    
    assert result is True
    mock_slack_client.files_upload_v2.assert_called_once()

def test_send_file_api_error(slack_service, mock_slack_client):
    """Test file sending API error."""
    mock_slack_client.files_upload_v2.side_effect = SlackApiError(
        "Error", {"error": "test error"}
    )
    slack_service.client = mock_slack_client
    
    with pytest.raises(APIError):
        slack_service.send_file("test.txt", "C123", "Test")

def test_get_users_all(slack_service, mock_slack_client):
    """Test getting all users."""
    slack_service.client = mock_slack_client
    
    users = slack_service.get_users()
    
    assert len(users) == 1
    assert users[0]['id'] == 'U123'
    mock_slack_client.users_list.assert_called_once()

def test_get_users_specific(slack_service, mock_slack_client):
    """Test getting specific user."""
    slack_service.client = mock_slack_client
    
    users = slack_service.get_users(user_id='U123')
    
    assert len(users) == 1
    assert users[0]['id'] == 'U123'
    mock_slack_client.users_info.assert_called_once()

def test_get_users_api_error(slack_service, mock_slack_client):
    """Test users API error."""
    mock_slack_client.users_list.side_effect = SlackApiError(
        "Error", {"error": "test error"}
    )
    slack_service.client = mock_slack_client
    
    with pytest.raises(APIError):
        slack_service.get_users()

def test_get_channels_all(slack_service, mock_slack_client):
    """Test getting all channels."""
    slack_service.client = mock_slack_client
    
    channels = slack_service.get_channels()
    
    assert len(channels) == 1
    assert channels[0]['id'] == 'C123'
    mock_slack_client.conversations_list.assert_called_once()

def test_get_channels_specific(slack_service, mock_slack_client):
    """Test getting specific channel."""
    slack_service.client = mock_slack_client
    
    channels = slack_service.get_channels(channel_id='C123')
    
    assert len(channels) == 1
    assert channels[0]['id'] == 'C123'
    mock_slack_client.conversations_info.assert_called_once()

def test_get_channels_api_error(slack_service, mock_slack_client):
    """Test channels API error."""
    mock_slack_client.conversations_list.side_effect = SlackApiError(
        "Error", {"error": "test error"}
    )
    slack_service.client = mock_slack_client
    
    with pytest.raises(APIError):
        slack_service.get_channels()

def test_search_messages(slack_service, mock_slack_client):
    """Test message search."""
    slack_service.client = mock_slack_client
    
    results = slack_service.search_messages("test")
    
    assert isinstance(results, list)
    mock_slack_client.search_messages.assert_called_once()

def test_search_messages_with_channel(slack_service, mock_slack_client):
    """Test message search in specific channel."""
    slack_service.client = mock_slack_client
    
    slack_service.search_messages("test", channel="C123")
    
    args = mock_slack_client.search_messages.call_args[1]
    assert args['channel'] == 'C123'

def test_search_messages_api_error(slack_service, mock_slack_client):
    """Test search API error."""
    mock_slack_client.search_messages.side_effect = SlackApiError(
        "Error", {"error": "test error"}
    )
    slack_service.client = mock_slack_client
    
    with pytest.raises(APIError):
        slack_service.search_messages("test")

def test_get_messages(slack_service):
    """Test getting messages from storage."""
    with patch.object(slack_service.storage, 'get_last_messages') as mock_get:
        mock_get.return_value = [{'message': 'test'}]
        
        messages = slack_service.get_messages(channel='C123')
        
        assert len(messages) == 1
        mock_get.assert_called_once()

def test_get_messages_no_channel(slack_service):
    """Test getting messages without channel."""
    with pytest.raises(ValidationError):
        slack_service.get_messages()