"erpnext_get_documents": erpnext_get_documents,
"erpnext_list_doctypes": erpnext_list_doctypes,
"erpnext_list_doctype_fields": erpnext_list_doctype_fields

    {
        "type": "function",
        "function": {
            "name": "erpnext_get_documents",
            "description": "Fetches a list of documents of the specified DocType or details of a specific document from the ERPNext system. Use list_doctypes and list_doctype_fields first to confirm available doctypes and fields",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_type": {
                        "type": "string",
                        "description": "The DocType you'd like to receive. The available options must only be from the list retrieved calling erpnext_list_doctypes"
                    },
                    "document_name": {
                        "type": "string",
                        "description": "Optional. The name (ID) of the document you'd like to receive its details. For example, CUST001 of type Customer."
                    },
                    "fields": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "The fields to include in the listing or document details. The available options must only be from the list retrieved by calling erpnext_list_doctype_fields. "
                    },
                    "filters": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "description": "Optional. Filters to apply to the listing, specified as SQL conditions."
                    },
                    "limit_page_length": {
                        "type": "integer",
                        "description": "Optional. The number of items to return at once. Default is 20."
                    },
                    "limit_start": {
                        "type": "integer",
                        "description": "Optional. The starting index for pagination. Default is 0."
                    }
                },
                "required": ["doc_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "erpnext_list_doctypes",
            "description": "Fetches a list of all DocTypes from the ERPNext system. This function retrieves all available document types, providing a comprehensive list of DocTypes for use in various ERPNext operations.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "erpnext_list_doctype_fields",
            "description": "Fetches a list of all fields for a specific DocType from the ERPNext system. This function retrieves the metadata of the specified document type, including field names, which can be used to understand the structure of the DocType.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctype_name": {
                        "type": "string",
                        "description": "The name of the DocType for which to fetch the fields."
                    }
                },
                "required": ["doctype_name"]
            }
        }
    }


def erpnext_get_documents(doc_type, document_name=None, fields=None, filters=None, limit_page_length=20, limit_start=0):
    """
    Fetch a list of documents of the specified DocType or details of a specific document.

    Parameters:
    - doc_type (str): The DocType you'd like to receive.
    - document_name (str): Optional. The name (ID) of the document you'd like to receive.
    - fields (list of str): Optional. The fields to include in the listing or document details.
    - filters (list of list): Optional. Filters to apply to the listing.
    - limit_page_length (int): Optional. The number of items to return at once. Default is 20.
    - limit_start (int): Optional. The starting index for pagination. Default is 0.

    Returns:
    - dict: The JSON response from the API or an error message.
    """
    
    api_key = erpnext_api_key
    api_secret = erpnext_api_secret
    base_url = "https://erp.cerenyi.ai"
    
    if document_name:
        url = f"{base_url}/api/resource/{doc_type}/{document_name}"
    else:
        url = f"{base_url}/api/resource/{doc_type}"
    
    headers = {
        "Authorization": f"token {api_key}:{api_secret}"
    }
    params = {
        "fields": json.dumps(fields) if fields else None,
        "filters": json.dumps(filters) if filters else None,
        "limit_page_length": limit_page_length,
        "limit_start": limit_start
    }
    # Remove None values from params
    params = {k: v for k, v in params.items() if v is not None}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            print(f"ERPNext Output: {json.dumps(response.json())}")
            return response.json()
        else:
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        error_message = f"An error occurred: {e}"
        print(error_message)
        return {"error": error_message}
        
        
def erpnext_list_doctypes():
    """
    Fetches a list of all DocTypes from the ERPNext system.

    Returns:
    - dict: The JSON response containing a list of all DocTypes.
    """
    try:
        result = erpnext_get_documents(doc_type="DocType", limit_page_length=1000)
        if "error" in result:
            return result  # return the error if it occurred
        doc_types = [doc["name"] for doc in result.get("data", [])]
        return {"doc_types": doc_types}
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        print(error_message)
        return {"error": error_message}
        

def erpnext_list_doctype_fields(doctype_name):
    """
    Fetches a list of all fields for a specific DocType from the ERPNext system.

    Parameters:
    - doctype_name (str): The name of the DocType for which to fetch the fields.

    Returns:
    - dict: The JSON response containing a list of all fields for the specified DocType.
    """
    try:
        result = erpnext_get_documents(doc_type="DocType", document_name=doctype_name)
        if "error" in result:
            return result  # return the error if it occurred
        fields = result.get("data", {}).get("fields", [])
        field_names = [field["fieldname"] for field in fields]
        return {"fields": field_names}
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        print(error_message)
        return {"error": error_message}
