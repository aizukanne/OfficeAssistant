"""Tests for external service function wrappers."""
import pytest
from unittest.mock import patch, MagicMock
from src.core.exceptions import ServiceError
from src.services.external.functions import (
    get_coordinates,
    get_weather_data,
    browse_internet,
    google_search,
    get_version
)

def test_get_version():
    """Test version retrieval."""
    version = get_version()
    assert isinstance(version, str)
    assert version == '1.0.0'

@pytest.fixture
def mock_service():
    """Create mock external service."""
    mock = MagicMock()
    mock.search.return_value = {'lat': 37.7749, 'lng': -122.4194}
    with patch('src.services.external.functions.get_instance', return_value=mock):
        yield mock

def test_get_coordinates_success(mock_service):
    """Test successful coordinates retrieval."""
    result = get_coordinates("San Francisco")
    assert result['lat'] == 37.7749
    assert result['lng'] == -122.4194
    mock_service.search.assert_called_once_with("coordinates of San Francisco")

def test_get_coordinates_error(mock_service):
    """Test coordinates retrieval error handling."""
    mock_service.search.side_effect = Exception("API Error")
    with pytest.raises(ServiceError) as exc:
        get_coordinates("Invalid Location")
    assert "API Error" in str(exc.value)
    assert exc.value.context['location'] == "Invalid Location"

def test_get_coordinates_recovery(mock_service):
    """Test coordinates retrieval with recovery."""
    mock_service.search.side_effect = [Exception("API Error"), {'lat': 0, 'lng': 0}]
    result = get_coordinates("San Francisco")
    assert result == {'error': 'Location not found'}

def test_get_weather_data_success(mock_service):
    """Test successful weather data retrieval."""
    mock_service.search.return_value = {
        'temperature': 20.5,
        'conditions': 'Sunny'
    }
    result = get_weather_data("London")
    assert result['temperature'] == 20.5
    assert result['conditions'] == 'Sunny'
    mock_service.search.assert_called_once_with("weather in London")

def test_get_weather_data_error(mock_service):
    """Test weather data retrieval error handling."""
    mock_service.search.side_effect = Exception("API Error")
    with pytest.raises(ServiceError) as exc:
        get_weather_data("Invalid Location")
    assert "API Error" in str(exc.value)
    assert exc.value.context['location'] == "Invalid Location"

def test_get_weather_data_recovery(mock_service):
    """Test weather data retrieval with recovery."""
    mock_service.search.side_effect = [Exception("API Error"), {'temperature': 0}]
    result = get_weather_data("London")
    assert result == {'error': 'Weather data unavailable'}

def test_browse_internet_success(mock_service):
    """Test successful internet browsing."""
    mock_service.search.return_value = [
        {'title': 'Test', 'url': 'http://example.com'}
    ]
    result = browse_internet("Python programming", full_text=True)
    assert len(result) == 1
    assert result[0]['title'] == 'Test'
    mock_service.search.assert_called_once_with(
        "Python programming",
        full_text=True
    )

def test_browse_internet_error(mock_service):
    """Test internet browsing error handling."""
    mock_service.search.side_effect = Exception("Search Error")
    with pytest.raises(ServiceError) as exc:
        browse_internet("Invalid Query")
    assert "Search Error" in str(exc.value)
    assert exc.value.context['query'] == "Invalid Query"

def test_browse_internet_recovery(mock_service):
    """Test internet browsing with recovery."""
    mock_service.search.side_effect = [Exception("Search Error"), []]
    result = browse_internet("Python")
    assert result == [{'error': 'Search failed'}]

def test_google_search_success(mock_service):
    """Test successful Google search."""
    mock_service.search.return_value = [
        {'title': 'Python', 'url': 'http://python.org'}
    ]
    result = google_search(
        "Python tutorial",
        before="2025-02-24",
        must_have="beginner"
    )
    assert len(result) == 1
    assert result[0]['title'] == 'Python'
    mock_service.search.assert_called_once_with(
        "Python tutorial",
        before="2025-02-24",
        must_have="beginner"
    )

def test_google_search_error(mock_service):
    """Test Google search error handling."""
    mock_service.search.side_effect = Exception("Search Error")
    with pytest.raises(ServiceError) as exc:
        google_search("Invalid Query")
    assert "Search Error" in str(exc.value)
    assert exc.value.context['query'] == "Invalid Query"

def test_google_search_recovery(mock_service):
    """Test Google search with recovery."""
    mock_service.search.side_effect = [Exception("Search Error"), []]
    result = google_search("Python")
    assert result == [{'error': 'Search failed'}]

def test_function_logging(mock_service, caplog):
    """Test function call logging."""
    get_coordinates("San Francisco")
    assert "Called get_coordinates" in caplog.text
    assert "duration=" in caplog.text

def test_error_context(mock_service):
    """Test error context preservation."""
    mock_service.search.side_effect = Exception("API Error")
    with pytest.raises(ServiceError) as exc:
        get_coordinates("Test Location")
    assert exc.value.context['location'] == "Test Location"
    assert "API Error" in str(exc.value)