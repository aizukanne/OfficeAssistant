import os
import json
import requests
from requests.exceptions import HTTPError, RequestException
from typing import Optional, Tuple, Dict, Any

def make_request(url: str, method: str = 'GET', headers: Optional[Dict] = None, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict:
    """
    Utility function to make HTTP requests and handle errors.
    
    Args:
        url: The URL for the request
        method: The HTTP method ('GET', 'POST', etc.)
        headers: The headers for the request
        params: The query parameters for the request
        data: The data to send in the request body
    
    Returns:
        Dict: The JSON response or an error message
    """
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            return {'status': 'error', 'message': 'Invalid HTTP method'}

        response.raise_for_status()
        return response.json()
    except HTTPError as http_err:
        return {'status': 'error', 'message': f'HTTP error occurred: {http_err}'}
    except RequestException as req_err:
        return {'status': 'error', 'message': f'Request error occurred: {req_err}'}
    except Exception as err:
        return {'status': 'error', 'message': f'An error occurred: {err}'}

def calendar_operations(access_token: str, calendar_id: str, operation: str, event_id: Optional[str] = None, event_data: Optional[Dict] = None) -> Dict:
    """
    Perform operations on Google Calendar.
    
    Args:
        access_token: Google OAuth access token
        calendar_id: ID of the calendar
        operation: Operation to perform ('read', 'create', 'update', 'delete')
        event_id: Optional ID of the event for update/delete operations
        event_data: Optional event data for create/update operations
        
    Returns:
        Dict: Operation result or error message
    """
    base_url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response_data = {}

    try:
        if operation == 'read':
            time_min = datetime.datetime.utcnow().isoformat() + 'Z'
            url = f"{base_url}/events?timeMin={time_min}"
            response_data = make_request(url, 'GET', headers=headers)

        elif operation == 'create':
            url = f"{base_url}/events"
            response_data = make_request(url, 'POST', headers=headers, data=event_data)

        elif operation == 'update':
            if event_id is None:
                raise ValueError("event_id is required for updating an event")
            url = f"{base_url}/events/{event_id}"
            response_data = make_request(url, 'PUT', headers=headers, data=event_data)

        elif operation == 'delete':
            if event_id is None:
                raise ValueError("event_id is required for deleting an event")
            url = f"{base_url}/events/{event_id}"
            response_data = make_request(url, 'DELETE', headers=headers)

        else:
            response_data['status'] = 'error'
            response_data['message'] = 'Invalid operation'

    except ValueError as ve:
        response_data['status'] = 'error'
        response_data['message'] = str(ve)

    return response_data

def exchange_auth_code_for_tokens(client_id: str, client_secret: str, authorization_code: str, redirect_uri: str) -> Dict:
    """
    Exchange authorization code for OAuth tokens.
    
    Args:
        client_id: OAuth client ID
        client_secret: OAuth client secret
        authorization_code: Authorization code to exchange
        redirect_uri: Redirect URI used in the OAuth flow
        
    Returns:
        Dict: OAuth tokens or error message
    """
    token_endpoint = 'https://oauth2.googleapis.com/token'
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': authorization_code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    return make_request(token_endpoint, 'POST', data=token_data)

def get_coordinates(location_name: str) -> Optional[Tuple[float, float]]:
    """
    Get geographical coordinates for a location.
    
    Args:
        location_name: Name of the location
        
    Returns:
        Optional[Tuple[float, float]]: Latitude and longitude if found
    """
    openweather_api_key = os.getenv('OPENWEATHER_KEY')
    base_url = 'http://api.openweathermap.org/geo/1.0/direct'
    params = {
        'q': location_name,
        'limit': 1,
        'appid': openweather_api_key
    }

    response = make_request(base_url, 'GET', params=params)
    if response.get('status') == 'error':
        return None

    data = response
    if data:
        lat = data[0]['lat']
        lon = data[0]['lon']
        return lat, lon
    return None

def get_weather_data(location_name: str = 'Whitehorse') -> Dict:
    """
    Get weather information for a location.
    
    Args:
        location_name: Name of the location (default: 'Whitehorse')
        
    Returns:
        Dict: Weather data or error message
    """
    openweather_api_key = os.getenv('OPENWEATHER_KEY')
    if not location_name.strip():
        return 'Location name is empty or contains only spaces. Please provide a valid location name.'

    coordinates = get_coordinates(location_name)
    if not coordinates:
        return 'Geolocation Failed! I could not find this location on a MAP.'

    lat, lon = coordinates
    url = 'https://api.openweathermap.org/data/3.0/onecall'
    params = {
        'appid': openweather_api_key,
        'lat': lat,
        'lon': lon,
        'exclude': 'hourly, minutely, daily',
        'units': 'metric'
    }

    response = make_request(url, 'GET', params=params)
    if response.get('status') == 'error':
        return f'Failed to get weather data: {response.get("message")}'

    return response