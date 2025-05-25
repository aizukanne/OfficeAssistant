#From tools.py  
    {
        "type": "function",
        "function": {
            "name": "get_models",
            "description": "Fetches the list of all models available in the Odoo instance, optionally filtered by a name pattern. A model represents a database table and defines the structure of the data stored within it. Each model typically corresponds to a specific business object or entity, such as customers, sales orders, products, invoices, etc..",
            "parameters": {
                "type": "object",
                "properties": {
                    "name_like": {
                        "type": "string",
                        "description": "A substring to filter the model names."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_fields",
            "description": "Fetches the fields of a specified model from the Odoo instance. This function handles authentication and then queries the Odoo API to retrieve the field information for the given model.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_name": {
                        "type": "string",
                        "description": "The technical name of the model whose fields are to be fetched."
                    }
                },
                "required": ["model_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_record",
            "description": "Creates new records in the specified model. Supports creation of single or multiple records. This function handles authentication and then sends a request to the Odoo API to create the records.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_name": {
                        "type": "string",
                        "description": "The technical name of the model."
                    },
                    "data": {
                        "type": ["object", "array"],
                        "items": {
                            "type": "object"
                        },
                        "description": "A dictionary or list of dictionaries of field names and values to create the record(s)."
                    },
                    "print_pdf": {
                        "type": "boolean",
                        "description": "Whether to return a download link to the PDF of the created document. Defaults to False."
                    }
                },
                "required": ["model_name", "data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_records",
            "description": "Fetches records from the specified model based on the given criteria. This function handles authentication and then sends a request to the Odoo API to retrieve the records. ",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_name": {
                        "type": "string",
                        "description": "The technical name of the model."
                    },
                    "criteria": {
                        "type": ["object", "array"],
                        "items": {
                            "type": "object"
                        },
                        "description": "A dictionary specifying the criteria for fetching records. Defaults to None."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Specifies how many records to fetch. Defaults to 20."
                    },
                    "fields_option": {
                        "type": "string",
                        "description": "Specifies verbosity of records fetched. Options are 'summary' to return only id and name fields and 'limited' to return fields specified in the limited_fields parameter. Defaults to 'summary'."
                    },
                    "limited_fields": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of fields to fetch if fields_option is 'limited'. Defaults to None."
                    }
                },
                "required": ["model_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_record",
            "description": "Updates an existing record in the specified model. This function handles authentication and then sends a request to the Odoo API to update the record.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_name": {
                        "type": "string",
                        "description": "The technical name of the model."
                    },
                    "record_id": {
                        "type": "integer",
                        "description": "The ID of the record to update."
                    },
                    "data": {
                        "type": "object",
                        "description": "A dictionary of field names and values to update."
                    }
                },
                "required": ["model_name", "record_id", "data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_records",
            "description": "Deletes records in the specified model based on criteria. This function handles authentication and then sends a request to the Odoo API to delete the records.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_name": {
                        "type": "string",
                        "description": "The technical name of the model."
                    },
                    "criteria": {
                        "type": "object",
                        "description": "A dictionary specifying the criteria for deletion."
                    }
                },
                "required": ["model_name", "criteria"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "print_record",
            "description": "Prints the specified record (subject to the record being printable). This function handles authentication and then sends a request to the Odoo API to generate a PDF of the record.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_name": {
                        "type": "string",
                        "description": "The technical name of the model."
                    },
                    "record_id": {
                        "type": "integer",
                        "description": "The ID of the document to print."
                    }
                },
                "required": ["model_name", "record_id"]
            }
        }
    }

#From lambda_function.py
        "get_models": get_models,
        "get_fields": get_fields,
        "create_record": create_record,
        "fetch_records": fetch_records,
        "update_record": update_record,
        "delete_records": delete_records,
        "print_record": print_record

#From Prompts.py
    "odoo_search": """
        1. Each search criterion must be represented as a dictionary, where:
           - The keys are the names of the fields.
           - Each key must contain an operator and a value.           
           - The values represent the conditions to evaluate those fields against.
        
        2. Each condition must include:
           - An "operator" specifying how the comparison should be performed (e.g., "=", ">=", "like").
           - A "value" representing what the field is being compared to (e.g., "value": 100).
        
        3. For example:
           - If there is a field named "customer_rank" and it needs to be greater than or equal to 1, the JSON structure would look like:
             {
               "customer_rank": {
                 "operator": ">=",
                 "value": 1
               }
             }
        
        4. Always enclose the entire criteria block in square brackets, even if there is only one criterion.
           - Example: 
             {
               "criteria": [
                 {
                   "customer_rank": {
                     "operator": ">=",
                     "value": 1
                   }
                 }
               ]
             }
        
        5. If you need to use "OR" logic for multiple conditions:
           - Include an "or" key whose value is a list of dictionaries.
           - Each dictionary represents one condition that must be evaluated.
           - Example:
             {
               "or": [
                 {
                   "name": {
                     "operator": "like",
                     "value": "Model"
                   }
                 },
                 {
                   "name": {
                     "operator": "like",
                     "value": "Azur"
                   }
                 }
               ]
             }
        
        6. Ensure that each condition inside the "or" block includes both:
           - An "operator".
           - A "value".
        
        7. Use square brackets to enclose criteria for handling both single and multiple conditions.
        
        8. Ensure that the structure reflects the logical flow of the search criteria.
           - Both simple conditions (e.g., single field comparisons) and complex conditions (e.g., multiple alternatives) should follow this format.
        
        9. When fetching details of records from Odoo, it is important to use the fields option 'limited' and specify the names of the fields you require to ensure the details are returned. Otherwise only the record name and id will be returned.

        10. Where a field has a 'selection' parameter, the only valid values for that field are the options listed in the selection paramter. Any other value will cause the request to fail.
        By following these steps, you can dynamically generate search criteria based on the fields, operators, and values provided in a request.
    """

    "odoo_search": """
        1. Each search criterion must be represented as a dictionary, where:
           - The keys are the names of the fields.
           - Each key must contain an operator and a value.           
           - The values represent the conditions to evaluate those fields against.
        
        2. Each condition must include:
           - An "operator" specifying how the comparison should be performed (e.g., "=", ">=", "like").
           - A "value" representing what the field is being compared to (e.g., "value": 100).
        
        3. For example:
           - If there is a field named "customer_rank" and it needs to be greater than or equal to 1, the JSON structure would look like:
             {
               "customer_rank": {
                 "operator": ">=",
                 "value": 1
               }
             }
        
        4. Always enclose the entire criteria block in square brackets, even if there is only one criterion.
           - Example: 
             {
               "criteria": [
                 {
                   "customer_rank": {
                     "operator": ">=",
                     "value": 1
                   }
                 }
               ]
             }
        
        5. If you need to use "OR" logic for multiple conditions:
           - Include an "or" key whose value is a list of dictionaries.
           - Each dictionary represents one condition that must be evaluated.
           - Example:
             {
               "or": [
                 {
                   "name": {
                     "operator": "like",
                     "value": "Model"
                   }
                 },
                 {
                   "name": {
                     "operator": "like",
                     "value": "Azur"
                   }
                 }
               ]
             }
        
        6. Ensure that each condition inside the "or" block includes both:
           - An "operator".
           - A "value".
        
        7. Use square brackets to enclose criteria for handling both single and multiple conditions.
        
        8. Ensure that the structure reflects the logical flow of the search criteria.
           - Both simple conditions (e.g., single field comparisons) and complex conditions (e.g., multiple alternatives) should follow this format.
        
        9. When fetching details of records from Odoo, it is important to use the fields option 'limited' and specify the names of the fields you require to ensure the details are returned. Otherwise only the record name and id will be returned.

        10. Where a field has a 'selection' parameter, the only valid values for that field are the options listed in the selection paramter. Any other value will cause the request to fail.
        By following these steps, you can dynamically generate search criteria based on the fields, operators, and values provided in a request.
        11. Where the intent of the user is ambiguous or is susceptible to misinterpretation, do not attempt to retrieve information from the ERP. Instead you must ask the user for clarification. Never assume what is not explicitly communicated in the request or subsequent clarification to avoid hallucination.
        12. In your response, explain what you did and what outcome was expected before giving the final response. It will allow the user understand where issues may have arisen and collaborate with you to resolve it.
    """

def get_models(name_like=None):
    """
    Fetches the list of all models available in the Odoo instance, optionally filtered by a name pattern.
    
    Args:
    - name_like (str, optional): A list containing substrings to filter the model names.
    
    Returns:
    - dict: A dictionary containing the available models or an error message.
    """
    auth_response = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
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
    - odoo_url (str): The base URL of the Odoo instance.
    - db (str): The database name.
    - login (str): The user's login name.
    - password (str): The user's password.
    - model_name (str): The technical name of the model whose fields are to be fetched.
    - required_only (bool): Whether to return only required fields. Default is False.
    - mini (bool): Whether to return only field string and type (applies only to fields_summary). Default is False.
    - summary (bool): Whether to use fields_summary endpoint. Default is False.

    Returns:
    - dict: A dictionary containing the fields of the specified model or an error message.
    """
    auth_response = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
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
    auth_response = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
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
    # Check if criteria is not already a list, if it's a dict, enclose it in a list
    if criteria is not None:
        if isinstance(criteria, dict):
            criteria = [criteria]
        elif not isinstance(criteria, list):
            return {'error': 'Invalid criteria format. Must be a dictionary or list of dictionaries.'}
    else:
        criteria = []

    auth_response = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
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
    auth_response = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
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
    auth_response = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
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


def fetch_data_from_api(query, limit=None, type=""):
    """
    Fetches data from the Odoo API endpoint using a provided SQL query.

    Args:
        odoo_url (str): The base URL of the Odoo instance.
        session_id (str): The session ID for authentication.
        query (str): The SQL query to execute.
        limit (int, optional): The maximum number of records to return. Defaults to 20.
        type (str, optional):  Indicates the type of request. Set to "schema" for schema requests. Defaults to "".

    Returns:
        dict: The JSON response from the API or an error message.
    """

    auth_response = authenticate(odoo_url, odoo_db, odoo_login, odoo_password)
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
        odoo_url (str): The base URL of the Odoo instance.
        session_id (str): The session ID for authentication.
        limit (int, optional): The maximum number of tables to return. Defaults to 120.

    Returns:
        dict: The JSON response containing the database schema or an error message.
    """
    if 'filter_string' == None:
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