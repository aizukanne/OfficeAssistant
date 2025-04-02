# External Services

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [← ERP Integrations](erp-integrations.md) | [Web and Search →](web-and-search.md)

The external services module in `extservices.py` provides functionality for interacting with various external APIs and services, enabling Maria to access calendar information, weather data, and other external resources.

## Overview

The external services module handles:

- Calendar operations
- OAuth token management
- Geolocation services
- Weather data retrieval
- External API integrations

## Calendar Operations

```python
def calendar_operations(access_token, calendar_id, operation, event_id=None, event_data=None)
```

This function performs operations on a calendar:

**Parameters:**
- `access_token`: The OAuth access token
- `calendar_id`: The ID of the calendar
- `operation`: The operation to perform (list, get, create, update, delete)
- `event_id`: (Optional) The ID of a specific event
- `event_data`: (Optional) Data for creating or updating an event

**Returns:**
- The result of the calendar operation

**Example:**
```python
# List events
events = calendar_operations(access_token, "primary", "list")

# Get a specific event
event = calendar_operations(access_token, "primary", "get", event_id="event123")

# Create an event
new_event = calendar_operations(
    access_token,
    "primary",
    "create",
    event_data={
        "summary": "Team Meeting",
        "location": "Conference Room 1",
        "description": "Weekly team meeting",
        "start": {"dateTime": "2023-01-15T10:00:00", "timeZone": "America/New_York"},
        "end": {"dateTime": "2023-01-15T11:00:00", "timeZone": "America/New_York"}
    }
)
```

**Example Usage:**

```
User: Schedule a team meeting for tomorrow at 10 AM
Maria: I'll schedule that for you. 
[Creates calendar event]
I've scheduled a team meeting for tomorrow (January 15) from 10:00 AM to 11:00 AM in Conference Room 1.
```

## OAuth Token Management

```python
def exchange_auth_code_for_tokens(client_id, client_secret, authorization_code, redirect_uri)
```

This function exchanges an authorization code for OAuth tokens:

**Parameters:**
- `client_id`: The OAuth client ID
- `client_secret`: The OAuth client secret
- `authorization_code`: The authorization code
- `redirect_uri`: The redirect URI

**Returns:**
- The OAuth tokens (access token, refresh token, etc.)

**Example:**
```python
tokens = exchange_auth_code_for_tokens(
    "client_id_123",
    "client_secret_456",
    "auth_code_789",
    "https://example.com/callback"
)
```

**Example Usage:**

```
User: Connect my Google Calendar
Maria: To connect your Google Calendar, please authorize access using this link:
[Authorization link]

User: [Completes authorization, providing code]
Maria: Thanks! I've connected to your Google Calendar. I can now help you manage your schedule.
```

## Geolocation Services

```python
def get_coordinates(location_name)
```

This function retrieves coordinates for a location:

**Parameters:**
- `location_name`: The name of the location

**Returns:**
- The latitude and longitude coordinates

**Example:**
```python
coordinates = get_coordinates("New York")
# Returns: {"lat": 40.7128, "lon": -74.0060}
```

**Example Usage:**

```
User: What's the weather like in Tokyo?
Maria: Let me check the weather in Tokyo for you.
[Gets coordinates for Tokyo, then retrieves weather data]
Currently in Tokyo, it's 22°C (72°F) and partly cloudy.
```

## Weather Data Retrieval

```python
def get_weather_data(location_name='Whitehorse')
```

This function retrieves weather data for a location:

**Parameters:**
- `location_name`: The name of the location (default: 'Whitehorse')

**Returns:**
- Weather data for the specified location

**Example:**
```python
weather = get_weather_data("London")
```

**Example Usage:**

```
User: What's the weather forecast for San Francisco this week?
Maria: Here's the weather forecast for San Francisco:

Today: 18°C (64°F), Sunny
Tomorrow: 17°C (63°F), Partly Cloudy
Wednesday: 16°C (61°F), Cloudy with a chance of rain
Thursday: 15°C (59°F), Light Rain
Friday: 16°C (61°F), Partly Cloudy
```

## Implementation Details

### Calendar Operations Implementation

```python
def calendar_operations(access_token, calendar_id, operation, event_id=None, event_data=None):
    """Perform operations on a calendar."""
    try:
        # Set up the API client
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        base_url = "https://www.googleapis.com/calendar/v3/calendars"
        
        # Perform the requested operation
        if operation == "list":
            # List events
            url = f"{base_url}/{calendar_id}/events"
            params = {
                "maxResults": 10,
                "singleEvents": True,
                "orderBy": "startTime",
                "timeMin": datetime.now().isoformat() + "Z"
            }
            response = requests.get(url, headers=headers, params=params)
        
        elif operation == "get":
            # Get a specific event
            url = f"{base_url}/{calendar_id}/events/{event_id}"
            response = requests.get(url, headers=headers)
        
        elif operation == "create":
            # Create an event
            url = f"{base_url}/{calendar_id}/events"
            response = requests.post(url, headers=headers, json=event_data)
        
        elif operation == "update":
            # Update an event
            url = f"{base_url}/{calendar_id}/events/{event_id}"
            response = requests.put(url, headers=headers, json=event_data)
        
        elif operation == "delete":
            # Delete an event
            url = f"{base_url}/{calendar_id}/events/{event_id}"
            response = requests.delete(url, headers=headers)
        
        else:
            logger.error(f"Unknown calendar operation: {operation}")
            return None
        
        # Check for errors
        if response.status_code not in [200, 201, 204]:
            logger.error(f"Calendar API error: {response.status_code} - {response.text}")
            return None
        
        # Return the response data
        if operation == "delete":
            return {"success": True}
        else:
            return response.json()
    
    except Exception as e:
        logger.error(f"Error in calendar_operations: {str(e)}")
        return None
```

### OAuth Token Exchange Implementation

```python
def exchange_auth_code_for_tokens(client_id, client_secret, authorization_code, redirect_uri):
    """Exchange an authorization code for OAuth tokens."""
    try:
        # Set up the token request
        url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": authorization_code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        
        # Make the request
        response = requests.post(url, data=data)
        
        # Check for errors
        if response.status_code != 200:
            logger.error(f"OAuth error: {response.status_code} - {response.text}")
            return None
        
        # Return the tokens
        return response.json()
    
    except Exception as e:
        logger.error(f"Error in exchange_auth_code_for_tokens: {str(e)}")
        return None
```

### Geolocation Implementation

```python
def get_coordinates(location_name):
    """Get coordinates for a location."""
    try:
        # Set up the geocoding request
        url = "https://api.openweathermap.org/geo/1.0/direct"
        params = {
            "q": location_name,
            "limit": 1,
            "appid": WEATHER_API_KEY
        }
        
        # Make the request
        response = requests.get(url, params=params)
        
        # Check for errors
        if response.status_code != 200:
            logger.error(f"Geocoding API error: {response.status_code} - {response.text}")
            return None
        
        # Parse the response
        data = response.json()
        
        if not data:
            logger.error(f"No location found for: {location_name}")
            return None
        
        # Return the coordinates
        return {
            "lat": data[0]["lat"],
            "lon": data[0]["lon"]
        }
    
    except Exception as e:
        logger.error(f"Error in get_coordinates: {str(e)}")
        return None
```

### Weather Data Implementation

```python
def get_weather_data(location_name='Whitehorse'):
    """Get weather data for a location."""
    try:
        # Get coordinates for the location
        coordinates = get_coordinates(location_name)
        
        if not coordinates:
            return None
        
        # Set up the weather request
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": coordinates["lat"],
            "lon": coordinates["lon"],
            "units": "metric",
            "appid": WEATHER_API_KEY
        }
        
        # Make the request
        response = requests.get(url, params=params)
        
        # Check for errors
        if response.status_code != 200:
            logger.error(f"Weather API error: {response.status_code} - {response.text}")
            return None
        
        # Return the weather data
        return response.json()
    
    except Exception as e:
        logger.error(f"Error in get_weather_data: {str(e)}")
        return None
```

## External API Integration

The external services module integrates with various APIs:

- **Google Calendar API**: For calendar operations
- **Google OAuth 2.0**: For authentication and token management
- **OpenWeatherMap API**: For weather data and geolocation
- **Other External APIs**: As needed for specific functionality

## Best Practices

When working with external services:

- Handle API rate limits and quotas
- Implement proper error handling
- Secure API keys and tokens
- Cache responses when appropriate
- Validate input data
- Handle timeouts and connection issues
- Respect API terms of service

## Future Enhancements

Planned enhancements for external services include:

- Integration with additional calendar providers
- Enhanced weather forecasting
- Travel and transportation services
- News and information services
- Financial data services
- Health and fitness tracking

---

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [← ERP Integrations](erp-integrations.md) | [Web and Search →](web-and-search.md)