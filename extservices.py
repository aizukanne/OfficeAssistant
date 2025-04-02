import os
import json
import nltk
import requests


from nltk.tokenize import sent_tokenize, word_tokenize


def calendar_operations(access_token, calendar_id, operation, event_id=None, event_data=None):
    base_url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response_data = {}

    try:
        if operation == 'read':
            # Read events
            time_min = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            url = f"{base_url}/events?timeMin={time_min}"
            response = requests.get(url, headers=headers)
            events = response.json().get('items', [])
            response_data['status'] = 'success'
            response_data['events'] = events

        elif operation == 'create':
            # Create an event
            url = f"{base_url}/events"
            response = requests.post(url, headers=headers, data=json.dumps(event_data))
            response_data['status'] = 'success'
            response_data['event_link'] = response.json().get('htmlLink')

        elif operation == 'update':
            # Update an existing event
            if event_id is None:
                raise ValueError("event_id is required for updating an event")
            url = f"{base_url}/events/{event_id}"
            response = requests.put(url, headers=headers, data=json.dumps(event_data))
            response_data['status'] = 'success'
            response_data['event_link'] = response.json().get('htmlLink')

        elif operation == 'delete':
            # Delete an event
            if event_id is None:
                raise ValueError("event_id is required for deleting an event")
            url = f"{base_url}/events/{event_id}"
            requests.delete(url, headers=headers)
            response_data['status'] = 'success'

        else:
            response_data['status'] = 'error'
            response_data['message'] = 'Invalid operation'

    except Exception as e:
        response_data['status'] = 'error'
        response_data['message'] = str(e)

    return response_data
    
    
def exchange_auth_code_for_tokens(client_id, client_secret, authorization_code, redirect_uri):
    # Endpoint for exchanging the authorization code for an access token
    token_endpoint = 'https://oauth2.googleapis.com/token'

    # Prepare the data for the token exchange
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': authorization_code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    # Make the request to get tokens
    response = requests.post(token_endpoint, data=token_data)
    tokens = response.json()

    # Check if the tokens are in the response
    if 'access_token' in tokens:
        return {
            'status': 'success',
            'access_token': tokens['access_token'],
            'refresh_token': tokens.get('refresh_token'),  # Refresh token is only provided on the first authorization 
            'expires_in': tokens['expires_in']  # The duration in seconds until the access token expires
        }
    else:
        return {
            'status': 'error',
            'error': tokens.get('error'),
            'error_description': tokens.get('error_description')
        }


def get_coordinates(location_name):
    openweather_api_key = os.getenv('OPENWEATHER_KEY')
    base_url = 'http://api.openweathermap.org/geo/1.0/direct'
    params = {
        'q': location_name,
        'limit': 1,  # You may limit to 1 result for accuracy
        'appid': openweather_api_key
    }
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            # Extract latitude and longitude from the first result
            lat = data[0]['lat']
            lon = data[0]['lon']
            return lat, lon
    return None  # Return None if location not found or API request fails
    
    
def get_weather_data(location_name='Whitehorse'):
    openweather_api_key = os.getenv('OPENWEATHER_KEY')
    # Validate location_name  
    if not location_name.strip():
        return 'Location name is empty or contains only spaces. Please provide a valid location name.'

    coordinates = get_coordinates(location_name)  # This function needs to be defined
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

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return f'Failed to get weather data: {response.reason}'

    return response.json()

