import json
import os
import urllib.request
import urllib.error
import requests
from botocore.exceptions import ClientError
from .auth_service import authenticate

# Import odoo_url from environment variables
odoo_url = os.getenv('ODOO_URL')

def get_models(name_like=None):
    """
    Fetches the list of all models available in the Odoo instance, optionally filtered by a name pattern.
    
    Args:
    - name_like (str, optional): A list containing substrings to filter the model names.
    
    Returns:
    - dict: A dictionary containing the available models or an error message.
    """
    auth_response = authenticate()
    if 'session_id' not in auth_response:
        return auth_response
    
    session_id = auth_response['session_id']
    endpoint = f"{odoo_url}/api/models"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    params = {}
    if name_like:
        params['names_list'] = name_like

    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}

def get_fields(model_name, required_only=False, mini=True, summary=True):
    """
    Fetches the fields of a specified model from the Odoo instance.

    Args:
    - model_name (str): The technical name of the model whose fields are to be fetched.
    - required_only (bool): Whether to return only required fields. Default is False.
    - mini (bool): Whether to return only field string and type (applies only to fields_summary). Default is False.
    - summary (bool): Whether to use fields_summary endpoint. Default is False.

    Returns:
    - dict: A dictionary containing the fields of the specified model or an error message.
    """
    auth_response = authenticate()
    if 'session_id' not in auth_response:
        return auth_response

    session_id = auth_response['session_id']
    endpoint = f"{odoo_url}/api/fields_summary" if summary else f"{odoo_url}/api/fields"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    params = {'object_type': model_name}
    
    if required_only:
        params['required_only'] = True
    if mini and summary:
        params['mini'] = True

    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}

def create_record(model_name, data, print_pdf=False):
    """
    Creates new records in the specified model. Supports creation of single or multiple records.
    
    Args:
    - model_name (str): The technical name of the model.
    - data (dict or list of dicts): A dictionary or list of dictionaries of field names and values to create the record(s).
    - print_pdf (bool, optional): Whether to return a download link to the PDF of the created document. Defaults to False.
    
    Returns:
    - dict: A dictionary containing the result of the creation or an error message.
    """
    auth_response = authenticate()
    if 'session_id' not in auth_response:
        return auth_response
    
    session_id = auth_response['session_id']
    endpoint = f"{odoo_url}/api/create"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    payload = {
        "params": {
            "object_type": model_name,
            "data": data
        }
    }
    if print_pdf:
        payload["params"]["print"] = print_pdf

    try:
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}

def fetch_records(model_name, criteria=None, limit=20, fields_option='summary', limited_fields=None):
    """
    Fetches records from the specified model based on the given criteria.
    
    Args:
    - model_name (str): The technical name of the model.
    - criteria (dict or list of dicts, optional): A dictionary specifying the criteria for fetching records. Defaults to None.
    - limit (int, optional): Specifies how many records to fetch. Defaults to 20.
    - fields_option (str, optional): Specifies verbosity of records fetched. Defaults to 'summary'.
    - limited_fields (list, optional): List of fields to fetch if fields_option is 'limited'. Defaults to None.
    
    Returns:
    - dict: A dictionary containing the fetched records or an error message.
    """
    if criteria is not None:
        if isinstance(criteria, dict):
            criteria = [criteria]
        elif not isinstance(criteria, list):
            return {'error': 'Invalid criteria format. Must be a dictionary or list of dictionaries.'}
    else:
        criteria = []

    auth_response = authenticate()
    if 'session_id' not in auth_response:
        return auth_response
    
    session_id = auth_response['session_id']
    endpoint = f"{odoo_url}/api/fetch"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    payload = {
        "params": {
            "object_type": model_name,
            "criteria": criteria,
            "limit": limit,
            "fields_option": fields_option
        }
    }
    if fields_option == 'limited' and limited_fields:
        payload["params"]["limited_fields"] = limited_fields

    print(f'Fetch Payload: {json.dumps(payload)}')
    try:
        response = requests.get(endpoint, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        response = response.json()
        response = sorted(response['result']['records'], key=lambda x: (x.get('name', ''), x['id']))
        return response
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}

def update_record(model_name, record_id, data):
    """
    Updates an existing record in the specified model.
    
    Args:
    - model_name (str): The technical name of the model.
    - record_id (int): The ID of the record to update.
    - data (dict): A dictionary of field names and values to update.
    
    Returns:
    - dict: A dictionary containing the result of the update or an error message.
    """
    auth_response = authenticate()
    if 'session_id' not in auth_response:
        return auth_response
    
    session_id = auth_response['session_id']
    endpoint = f"{odoo_url}/api/update"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    payload = {
        "params": {
            "object_type": model_name,
            "id": record_id,
            "data": data
        }
    }

    try:
        response = requests.put(endpoint, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}

def delete_records(model_name, criteria):
    """
    Deletes records in the specified model based on criteria.
    
    Args:
    - model_name (str): The technical name of the model.
    - criteria (dict): A dictionary specifying the criteria for deletion.
    
    Returns:
    - dict: A dictionary containing the result of the deletion or an error message.
    """
    auth_response = authenticate()
    if 'session_id' not in auth_response:
        return auth_response
    
    session_id = auth_response['session_id']
    endpoint = f"{odoo_url}/api/delete"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    payload = {
        "params": {
            "object_type": model_name,
            "criteria": criteria
        }
    }

    try:
        response = requests.delete(endpoint, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}

def print_record(model_name, record_id):
    """
    Prints the specified record (subject to the record being printable).
    
    Args:
    - model_name (str): The technical name of the model.
    - record_id (int): The ID of the document to print.
    
    Returns:
    - dict: A dictionary containing the result of the print request or an error message.
    """
    auth_response = authenticate()
    if 'session_id' not in auth_response:
        return auth_response
    
    session_id = auth_response['session_id']
    endpoint = f"{odoo_url}/api/generate_pdf"
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session_id={session_id}'
    }
    payload = {
        "params": {
            "object_type": model_name,
            "id": record_id
        }
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(endpoint, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req) as resp:
            response_data = resp.read().decode()
            print(f"Response content: {response_data}")  # Log response content for debugging
            return json.loads(response_data)
    except urllib.error.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}'}
    except json.JSONDecodeError as json_err:
        return {'error': f'JSON decode error occurred: {json_err} - Response content: {response_data}'}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}

def fetch_data_from_api(query, limit=None, type=""):
    """
    Fetches data from the Odoo API endpoint using a provided SQL query.

    Args:
        query (str): The SQL query to execute.
        limit (int, optional): The maximum number of records to return. Defaults to 20.
        type (str, optional):  Indicates the type of request. Set to "schema" for schema requests. Defaults to "".

    Returns:
        dict: The JSON response from the API or an error message.
    """
    auth_response = authenticate()
    if 'session_id' not in auth_response:
        return auth_response
    
    session_id = auth_response['session_id']

    endpoint = f"{odoo_url}/api/fetch_sql"
    headers = {'Content-Type': 'application/json', 'Cookie': f'session_id={session_id}'}
    query = query.rstrip(';')
    payload = {"params": {"query": query}}
    if limit is not None:
        payload["params"]["limit"] = limit
    if type:
        payload["params"]["type"] = type

    print(f"SQL Query: {json.dumps(payload)}")
    try:
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {'error': f'HTTP error occurred: {http_err}', 'status_code': response.status_code, 'response_text': response.text}
    except Exception as err:
        return {'error': f'Other error occurred: {err}'}

def get_database_schema(filter_string=None, limit=120):
    """
    Fetches the database schema information from the Odoo API.

    Args:
        filter_string (str, optional): A text pattern that matches part of a table name.
        limit (int, optional): The maximum number of tables to return. Defaults to 120.

    Returns:
        dict: The JSON response containing the database schema or an error message.
    """
    if filter_string is None:
        return """A filter string is required. The filter_string should be a text pattern that matches part of a table name. For example, if you want to find tables related to customers, use 'Customer'. The search is case-insensitive and will match any table name containing your pattern anywhere in its name. The pattern can be a full word or part of a word."""

    # Clean the input string
    filter_string = filter_string.strip().replace("'", "''")  # Escape single quotes

    schema_query =  f"""
    SELECT 
        table_schema,
        table_name,
        string_agg(
            column_name || ' (' || data_type || 
            CASE WHEN is_nullable = 'YES' THEN ', nullable' ELSE '' END ||
            CASE WHEN column_default IS NOT NULL THEN ', default: ' || column_default ELSE '' END
            || ')', 
            E'\n'
            ORDER BY ordinal_position
        ) as columns
    FROM information_schema.columns
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    AND table_name ILIKE '%{filter_string}%'
    GROUP BY table_schema, table_name
    ORDER BY table_schema, table_name
    """
    return fetch_data_from_api(schema_query, limit=limit, type="schema")