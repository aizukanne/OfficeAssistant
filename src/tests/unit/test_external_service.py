import pytest
import aiohttp
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.external_services import ExternalService
from src.core.exceptions import (
    APIError,
    NetworkError,
    TimeoutError,
    ValidationError
)

@pytest.fixture
def external_service():
    """Create ExternalService instance."""
    return ExternalService()

@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp ClientSession."""
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.headers = {'Content-Type': 'text/html'}
    mock_response.charset = 'utf-8'
    mock_response.text.return_value = "<html><body>Test content</body></html>"
    mock_response.read.return_value = b"Test binary content"
    mock_session.get.return_value.__aenter__.return_value = mock_response
    return mock_session

def test_initialization(external_service):
    """Test service initialization."""
    assert external_service.logger is not None
    assert external_service.proxy_url is not None
    assert external_service.stopwords is not None
    assert external_service.timeout > 0
    assert external_service.max_retries > 0
    assert external_service.retry_delay > 0

def test_validate_config_missing_keys(external_service):
    """Test configuration validation with missing keys."""
    with patch.dict('os.environ', {}, clear=True):
        missing = external_service.validate_config()
        assert 'GOOGLE_API_KEY' in missing
        assert 'GOOGLE_SEARCH_CX' in missing

def test_validate_config_valid(external_service):
    """Test configuration validation with valid keys."""
    with patch.dict('os.environ', {
        'GOOGLE_API_KEY': 'test_key',
        'GOOGLE_SEARCH_CX': 'test_cx'
    }):
        missing = external_service.validate_config()
        assert not missing

@pytest.mark.asyncio
async def test_fetch_content_html(external_service, mock_aiohttp_session):
    """Test fetching HTML content."""
    with patch('aiohttp.ClientSession', return_value=mock_aiohttp_session):
        content, content_type = await external_service.fetch_content('http://example.com')
        assert content == "<html><body>Test content</body></html>"
        assert content_type == 'text/html'

@pytest.mark.asyncio
async def test_fetch_content_pdf(external_service, mock_aiohttp_session):
    """Test fetching PDF content."""
    mock_aiohttp_session.get.return_value.__aenter__.return_value.headers = {
        'Content-Type': 'application/pdf'
    }
    
    with patch('aiohttp.ClientSession', return_value=mock_aiohttp_session):
        content, content_type = await external_service.fetch_content('http://example.com/test.pdf')
        assert content == b"Test binary content"
        assert content_type == 'application/pdf'

@pytest.mark.asyncio
async def test_fetch_content_timeout(external_service):
    """Test fetch content timeout."""
    mock_session = AsyncMock()
    mock_session.get.side_effect = asyncio.TimeoutError()
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        with pytest.raises(TimeoutError):
            await external_service.fetch_content('http://example.com')

@pytest.mark.asyncio
async def test_fetch_content_network_error(external_service):
    """Test fetch content network error."""
    mock_session = AsyncMock()
    mock_session.get.side_effect = aiohttp.ClientConnectorSSLError(None, None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        with pytest.raises(NetworkError):
            await external_service.fetch_content('http://example.com')

@pytest.mark.asyncio
async def test_process_content_html(external_service):
    """Test processing HTML content."""
    html_content = """
    <html>
        <body>
            <p>Test paragraph 1</p>
            <p>Test paragraph 2</p>
            <meta name="author" content="Test Author">
            <meta property="article:published_time" content="2025-02-22">
        </body>
    </html>
    """
    
    result = await external_service.process_content(
        html_content,
        'text/html',
        full_text=False
    )
    
    assert len(result) == 1
    assert result[0]['type'] == 'text'
    assert 'summary' in result[0]['text']
    assert result[0]['text']['author'] == 'Test Author'

@pytest.mark.asyncio
async def test_process_content_document(external_service):
    """Test processing document content."""
    mock_storage = MagicMock()
    mock_storage.upload_to_s3.return_value = 'https://test-bucket.s3.amazonaws.com/test.pdf'
    
    with patch('src.services.external_services._storage_service', mock_storage):
        
        result = await external_service.process_content(
            b"Test PDF content",
            'application/pdf',
            full_text=False
        )
        
        assert len(result) == 1
        assert result[0]['type'] == 'text'
        assert 'Document available for download' in result[0]['text']['summary']
        assert 's3_url' in result[0]['text']

def test_search_basic(external_service):
    """Test basic search functionality."""
    with patch.object(external_service, 'make_request') as mock_request:
        mock_request.return_value = {
            'items': [
                {'link': 'http://example1.com'},
                {'link': 'http://example2.com'}
            ]
        }
        
        with patch.object(external_service, '_process_urls') as mock_process:
            mock_process.return_value = [{'type': 'text', 'text': {'summary': 'Test'}}]
            
            results = external_service.search('test query')
            
            assert len(results) == 1
            assert results[0]['type'] == 'text'
            assert results[0]['text']['summary'] == 'Test'

def test_search_with_filters(external_service):
    """Test search with additional filters."""
    with patch.object(external_service, 'make_request') as mock_request:
        mock_request.return_value = {'items': [{'link': 'http://example.com'}]}
        
        with patch.object(external_service, '_process_urls') as mock_process:
            external_service.search(
                'test query',
                before='2025-02-22',
                after='2025-02-21',
                intext='specific text',
                must_have='exact phrase'
            )
            
            # Verify the search query includes all filters
            args = mock_request.call_args[1]['params']['q']
            assert 'before:2025-02-22' in args
            assert 'after:2025-02-21' in args
            assert 'intext:specific text' in args
            assert '"exact phrase"' in args

def test_search_error_handling(external_service):
    """Test search error handling."""
    with patch.object(external_service, 'make_request') as mock_request:
        mock_request.return_value = {'status': 'error', 'message': 'API error'}
        
        with pytest.raises(APIError):
            external_service.search('test query')

@pytest.mark.asyncio
async def test_process_urls_concurrent(external_service):
    """Test concurrent URL processing."""
    urls = ['http://example1.com', 'http://example2.com']
    
    with patch.object(external_service, '_process_single_url') as mock_process:
        mock_process.return_value = [{'type': 'text', 'text': {'summary': 'Test'}}]
        
        results = await external_service._process_urls(urls)
        
        assert len(results) == 2
        assert mock_process.call_count == 2

@pytest.mark.asyncio
async def test_process_single_url_error(external_service):
    """Test single URL processing error handling."""
    with patch.object(external_service, 'fetch_content') as mock_fetch:
        mock_fetch.side_effect = Exception('Test error')
        
        result = await external_service._process_single_url(
            MagicMock(),
            'http://example.com',
            asyncio.Semaphore(1),
            False
        )
        
        assert len(result) == 1
        assert result[0]['type'] == 'text'
        assert 'error' in result[0]['text']
        assert 'Test error' in result[0]['text']['error']