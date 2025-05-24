import requests
import json
import urllib.request
import urllib.error
from botocore.exceptions import ClientError

odoo_url = "http://167.71.140.93:8069"
odoo_db = "Production"
odoo_login = "ai_bot"
odoo_password = "Carbon123#"
base_url = odoo_url

#############################################################################################################
# Odoo Functions
#############################################################################################################

def authenticate(odoo_url, odoo_db, odoo_login, odoo_password):
    """
    Authenticates the user and returns a session cookie.
    
    Args:
    - odoo_url (str): The base URL of the Odoo instance.
    - odoo_db (str): The database name.
    - odoo_login (str): The user's login name.
    - odoo_password (str): The user's password.
    
    Returns:
    - dict: A dictionary containing the session cookie or an error message.
    """
    endpoint = f"{odoo_url}/web/session/authenticate"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "params": {
            "db": odoo_db,
            "login": odoo_login,
            "password": odoo_password
        }
    }

    try:
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        session_id = response.cookies.get('session_id')
        if session_id:
            return {'session_id': session_id}
        else:
            return {'error': 'Authentication failed. No session ID returned.'}
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}
        

def odoo_get_mapped_models(include_fields=True, model_name=None):
    """
    Fetches available mapped models.
    
    Args:
    - include_fields (bool): Whether to include field mappings.
    - model_name (str): Optional filter for model names.
    
    Returns:
    - dict: Response containing mapped models.
    """
    # Authenticate first
    auth_result = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
    if 'error' in auth_result:
        return auth_result
    
    session_id = auth_result['session_id']
    endpoint = f"{base_url}/api/mapped_models"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    params = {}
    payload = {}
    
    if include_fields:
        params['include_fields'] = include_fields
    if model_name:
        params['model_name'] = model_name
    payload['params'] = params
    try: 
        print(json.dumps(payload))
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}


def odoo_get_mapped_fields(model):
    """
    Fetches field mappings for a specific external model.
    
    Args:
    - model (str): External model name.
    
    Returns:
    - dict: Response containing field mappings.
    """
    # Authenticate first
    auth_result = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
    if 'error' in auth_result:
        return auth_result
    
    session_id = auth_result['session_id']
    endpoint = f"{base_url}/api/mapped_fields"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    payload = {'model': model}
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}


def odoo_fetch_records(external_model, filters=None):
    """
    Retrieves records from an external model.
    
    Args:
    - base_url (str): Base URL for the API middleware.
    - odoo_url (str): The base URL of the Odoo instance.
    - db (str): The database name.
    - login (str): The user's login name.
    - password (str): The user's password.
    - external_model (str): External model name.
    - filters (list): Optional Odoo domain filters.
    
    Returns:
    - dict: Response containing records.
    """
    # Authenticate first
    auth_result = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
    if 'error' in auth_result:
        return auth_result
    
    session_id = auth_result['session_id']
    endpoint = f"{base_url}/api/{external_model}"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    payload = {}
    
    if filters:
        payload['filters'] = filters
        
    try:
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}


def odoo_create_record(external_model, record_data):
    """
    Creates a new record.
    Args:
        external_model (str): External model name.
        record_data (dict): Data for the record to be created.
    Returns:
        dict: Response containing the created record or error.
    """
    # Check for missing parameters
    if not external_model:
        return {'error': "Missing required parameter: 'external_model'."}
    if not record_data:
        return {'error': "Missing required parameter: 'record_data'."}
    if not isinstance(record_data, dict):
        return {'error': "'record_data' must be a dictionary."}
    
    # Authenticate first
    auth_result = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
    if 'error' in auth_result:
        return auth_result
    session_id = auth_result['session_id']
    endpoint = f"{base_url}/api/{external_model}/create"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    payload = {'params': record_data}
    try:
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}


def odoo_update_record(external_model, record_id, **kwargs):
    """
    Updates an existing record.
    Args:
    - external_model (str): External model name.
    - record_id (int): ID of the record to update.
    - **kwargs: Variable keyword arguments that will be combined into record_data.
    
    Returns:
    - dict: Response containing the updated record.
    """
    # Authenticate first
    auth_result = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
    if 'error' in auth_result:
        return auth_result
    
    session_id = auth_result['session_id']
    endpoint = f"{base_url}/api/{external_model}/update/{record_id}"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    
    # Using kwargs directly as the record_data
    record_data = kwargs
    
    try:
        response = requests.put(endpoint, headers=headers, json=record_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}


def odoo_delete_record(external_model, record_id):
    """
    Deletes a record.
    
    Args:
    - base_url (str): Base URL for the API middleware.
    - odoo_url (str): The base URL of the Odoo instance.
    - db (str): The database name.
    - login (str): The user's login name.
    - password (str): The user's password.
    - external_model (str): External model name.
    - record_id (int): ID of the record to delete.
    
    Returns:
    - dict: Response indicating success or failure.
    """
    # Authenticate first
    auth_result = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
    if 'error' in auth_result:
        return auth_result
    
    session_id = auth_result['session_id']
    endpoint = f"{base_url}/api/{external_model}/delete/{record_id}"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    
    try:
        response = requests.delete(endpoint, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}