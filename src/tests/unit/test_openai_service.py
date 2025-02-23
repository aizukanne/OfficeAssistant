import pytest
from unittest.mock import patch, MagicMock
from openai.error import RateLimitError, APIError as OpenAIAPIError

from src.services.openai_service import OpenAIService
from src.core.exceptions import (
    APIError,
    ValidationError,
    AuthenticationError,
    RateLimitError as AppRateLimitError
)

@pytest.fixture
def openai_service():
    """Create OpenAIService instance."""
    return OpenAIService()

@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    mock = MagicMock()
    
    # Mock ChatCompletion
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
    mock.ChatCompletion.create.return_value = mock_response
    
    # Mock Embedding
    mock.Embedding.create.return_value = {
        'data': [{'embedding': [0.1, 0.2, 0.3]}]
    }
    
    # Mock Image
    mock.Image.create.return_value = MagicMock(
        data=[MagicMock(url="https://example.com/image.jpg")]
    )
    
    # Mock Model
    mock.Model.list.return_value = MagicMock(
        data=[{'id': 'test-model', 'owned_by': 'openai'}]
    )
    mock.Model.retrieve.return_value = {
        'id': 'test-model',
        'owned_by': 'openai'
    }
    
    return mock

def test_initialization(openai_service):
    """Test service initialization."""
    assert openai_service.logger is not None

def test_initialization_error():
    """Test initialization error handling."""
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(AuthenticationError):
            OpenAIService()

def test_validate_config_missing_key(openai_service):
    """Test configuration validation with missing key."""
    with patch.dict('os.environ', {}, clear=True):
        missing = openai_service.validate_config()
        assert 'OPENAI_API_KEY' in missing

def test_validate_config_valid(openai_service):
    """Test configuration validation with valid key."""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
        missing = openai_service.validate_config()
        assert not missing

def test_generate_content_success(openai_service, mock_openai):
    """Test successful content generation."""
    with patch('openai.ChatCompletion', mock_openai.ChatCompletion):
        response = openai_service.generate_content("Test prompt")
        assert response == "Test response"
        mock_openai.ChatCompletion.create.assert_called_once()

def test_generate_content_empty_prompt(openai_service):
    """Test generation with empty prompt."""
    with pytest.raises(ValidationError):
        openai_service.generate_content("")

def test_generate_content_rate_limit(openai_service, mock_openai):
    """Test generation rate limit error."""
    mock_openai.ChatCompletion.create.side_effect = RateLimitError()
    
    with patch('openai.ChatCompletion', mock_openai.ChatCompletion):
        with pytest.raises(AppRateLimitError):
            openai_service.generate_content("Test prompt")

def test_generate_content_api_error(openai_service, mock_openai):
    """Test generation API error."""
    mock_openai.ChatCompletion.create.side_effect = OpenAIAPIError()
    
    with patch('openai.ChatCompletion', mock_openai.ChatCompletion):
        with pytest.raises(APIError):
            openai_service.generate_content("Test prompt")

def test_get_embedding_success(openai_service, mock_openai):
    """Test successful embedding generation."""
    with patch('openai.Embedding', mock_openai.Embedding):
        embedding = openai_service.get_embedding("Test text")
        assert embedding == [0.1, 0.2, 0.3]
        mock_openai.Embedding.create.assert_called_once()

def test_get_embedding_rate_limit(openai_service, mock_openai):
    """Test embedding rate limit error."""
    mock_openai.Embedding.create.side_effect = RateLimitError()
    
    with patch('openai.Embedding', mock_openai.Embedding):
        with pytest.raises(AppRateLimitError):
            openai_service.get_embedding("Test text")

def test_get_embedding_api_error(openai_service, mock_openai):
    """Test embedding API error."""
    mock_openai.Embedding.create.side_effect = OpenAIAPIError()
    
    with patch('openai.Embedding', mock_openai.Embedding):
        with pytest.raises(APIError):
            openai_service.get_embedding("Test text")

def test_analyze_content_success(openai_service, mock_openai):
    """Test successful content analysis."""
    mock_response = """
    Main topics
    - Topic 1
    - Topic 2
    
    Sentiment
    Positive
    
    Key entities
    - Entity 1
    - Entity 2
    
    Summary
    Test summary
    
    Language complexity score: 7
    """
    mock_openai.ChatCompletion.create.return_value.choices[0].message.content = mock_response
    
    with patch('openai.ChatCompletion', mock_openai.ChatCompletion):
        result = openai_service.analyze_content("Test content")
        
        assert isinstance(result, dict)
        assert 'topics' in result
        assert 'sentiment' in result
        assert 'entities' in result
        assert 'summary' in result
        assert 'complexity_score' in result

def test_analyze_content_parse_error(openai_service, mock_openai):
    """Test content analysis parse error."""
    mock_openai.ChatCompletion.create.return_value.choices[0].message.content = "Invalid format"
    
    with patch('openai.ChatCompletion', mock_openai.ChatCompletion):
        result = openai_service.analyze_content("Test content")
        
        assert 'error' in result
        assert 'raw_response' in result

def test_generate_image_success(openai_service, mock_openai):
    """Test successful image generation."""
    with patch('openai.Image', mock_openai.Image):
        urls = openai_service.generate_image("Test prompt")
        assert len(urls) == 1
        assert urls[0] == "https://example.com/image.jpg"
        mock_openai.Image.create.assert_called_once()

def test_generate_image_rate_limit(openai_service, mock_openai):
    """Test image generation rate limit error."""
    mock_openai.Image.create.side_effect = RateLimitError()
    
    with patch('openai.Image', mock_openai.Image):
        with pytest.raises(AppRateLimitError):
            openai_service.generate_image("Test prompt")

def test_generate_image_api_error(openai_service, mock_openai):
    """Test image generation API error."""
    mock_openai.Image.create.side_effect = OpenAIAPIError()
    
    with patch('openai.Image', mock_openai.Image):
        with pytest.raises(APIError):
            openai_service.generate_image("Test prompt")

def test_list_models_success(openai_service, mock_openai):
    """Test successful models listing."""
    with patch('openai.Model', mock_openai.Model):
        models = openai_service.list_models()
        assert len(models) == 1
        assert models[0]['id'] == 'test-model'
        mock_openai.Model.list.assert_called_once()

def test_list_models_api_error(openai_service, mock_openai):
    """Test models listing API error."""
    mock_openai.Model.list.side_effect = OpenAIAPIError()
    
    with patch('openai.Model', mock_openai.Model):
        with pytest.raises(APIError):
            openai_service.list_models()

def test_get_model_success(openai_service, mock_openai):
    """Test successful model retrieval."""
    with patch('openai.Model', mock_openai.Model):
        model = openai_service.get_model('test-model')
        assert model['id'] == 'test-model'
        mock_openai.Model.retrieve.assert_called_once()

def test_get_model_api_error(openai_service, mock_openai):
    """Test model retrieval API error."""
    mock_openai.Model.retrieve.side_effect = OpenAIAPIError()
    
    with patch('openai.Model', mock_openai.Model):
        with pytest.raises(APIError):
            openai_service.get_model('test-model')