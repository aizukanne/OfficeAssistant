import requests
from requests.exceptions import HTTPError, RequestException

def make_request(url, method='GET', headers=None, params=None, data=None):
    """
    Utility function to make HTTP requests and handle errors.
    
    Args:
    - url (str): The URL for the request.
    - method (str): The HTTP method ('GET', 'POST', etc.).
    - headers (dict): The headers for the request.
    - params (dict): The query parameters for the request.
    - data (dict): The data to send in the request body.
    
    Returns:
    - dict: The JSON response or an error message.
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

tools = [
    {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": "Performs a Google search and retrieves web content for the top five results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "The primary term to search for."
                    },
                    "before": {
                        "type": "string",
                        "description": "Filters results to only those before a specified date (format: YYYY-MM-DD)."
                    },
                    "after": {
                        "type": "string",
                        "description": "Filters results to only those after a specified date (format: YYYY-MM-DD)."
                    },
                    "intext": {
                        "type": "string",
                        "description": "Search for pages that include a specific word in their content."
                    },
                    "allintext": {
                        "type": "string",
                        "description": "Search for pages that include all specified words somewhere in their content."
                    },
                    "and_condition": {
                        "type": "string",
                        "description": "Search for results related to multiple specified terms."
                    },
                    "must_have": {
                        "type": "string",
                        "description": "Search for results that must include the exact phrase specified."
                    }
                },
                "required": ["search_term"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browse_internet",
            "description": "Extracts and refines web content from a list of URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "A single URL from which to retrieve and return content."
                        },
                        "description": "A list of URLs to read and process."
                    },
                    "full_text": {
                        "type": "boolean",
                        "description": "If True, retrieves the full text of the articles. If False or omitted, retrieves a summary of each article. Default is False."
                    }
                },
                "required": ["urls"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_coordinates",
            "description": "Retrieves geographical coordinates (latitude and longitude) for a given location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_name": {
                        "type": "string",
                        "description": "The name of the location to find coordinates for."
                    }
                },
                "required": ["location_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_data",
            "description": "Obtains weather information for a given location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_name": {
                        "type": "string",
                        "default": "Fredericton",
                        "description": "The name of the location to get weather data for. Defaults to 'Fredericton' if not specified."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_message_by_sort_id",
            "description": "Retrieves the details of a specific message from a DynamoDB table based on its sort key identifier.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "description": "The role of the entity that sent the message, either user or assistant."
                    },
                    "sort_id": {
                        "type": "number",
                        "description": "The unique sort key identifier of the message to retrieve."
                    },
                    "chat_id": {
                        "type": "string",
                        "description": "The unique chat key identifier of the message to retrieve."
                    }                    
                },
                "required": ["role", "chat_id", "sort_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_messages_in_range",
            "description": "Retrieves the summary of a range of messages from a DynamoDB table based on the sort key range provided.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "The unique chat identifier."
                    },
                    "start_sort_id": {
                        "type": "number",
                        "description": "The starting point of the sort key range."
                    },
                    "end_sort_id": {
                        "type": "number",
                        "description": "The ending point of the sort key range."
                    }
                },
                "required": ["chat_id", "start_sort_id", "end_sort_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_embedding",
            "description": "Processes a given text string to clean it up and then generates an embedding using OpenAI's embedding model.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text string to be processed and converted into an embedding."
                    },
                    "model": {
                        "type": "string",
                        "default": "text-embedding-ada-002",
                        "description": "The specific OpenAI embedding model to use for generating the text embedding."
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_slack_message",
            "description": "Relays a message to a Slack user based on their real name or display name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to be sent to the user."
                    },
                    "channel": {
                        "type": "string",
                        "description": "The user_id or channel_id of the user to send the message to."
                    }
                },
                "required": ["message", "channel"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_users",
            "description": "Returns a list of all users with their user_id, display_name and email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The optional user ID of the specific user to retrieve."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_audio_to_slack",
            "description": "Sends a response to the user as an audio message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "The ID of the Slack channel where the file will be uploaded."
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to be converted to speech and uploaded as an audio file."
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_file_to_slack",
            "description": "Sends a file to a specified Slack channel or user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file to be uploaded."
                    },
                    "chat_id": {
                        "type": "string",
                        "description": "The ID of the Slack channel where the file will be uploaded."
                    },
                    "title": {
                        "type": "string",
                        "description": "The title of the file to be uploaded."
                    },
                    "ts": {
                        "type": "string",
                        "description": "Optional. The thread timestamp (ts) to reply in a thread."
                    }
                },
                "required": ["file_path", "chat_id", "title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_as_pdf",
            "description": "Converts formatted text to a PDF and uploads it to a specified Slack channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to be converted to PDF."
                    },
                    "chat_id": {
                        "type": "string",
                        "description": "The ID of the Slack channel where the PDF will be uploaded."
                    },
                    "title": {
                        "type": "string",
                        "description": "The title of the PDF file to be uploaded."
                    },
                    "ts": {
                        "type": "string",
                        "description": "Optional. The thread timestamp (ts) to reply in a thread."
                    }
                },
                "required": ["text", "chat_id", "title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lists the files available on the system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_prefix": {
                        "type": "string",
                        "description": "Optional. The name of the folder whose files you want to list."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_channels",
            "description": "Retrieves a list of all slack channels on this slack workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "The optional channel ID of the specific user to retrieve."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_openai_o1",
            "description": "Sends a text prompt to the Openai o1 advanced reasoning LLM API and retrieves the generated content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The text prompt to be sent to the o1 API for analysis and content generation."
                    }
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_mute_status",
            "description": "Sets or checks the mute status for the chat.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": ["boolean", "null"],
                        "description": "The boolean value to set for the 'maria_status' attribute."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "solve_maths",
            "description": "Executes the provided Python code with the given parameters and returns the result.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python code to be executed."
                    },
                    "params": {
                        "type": "object",
                        "description": "A dictionary of parameters that the code may require."
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_models",
            "description": "Fetches the list of all models available in the Odoo instance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name_like": {
                        "type": "object",
                        "description": "A list of substrings to filter the model names."
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
            "description": "Fetches the fields of a specified model from the Odoo instance.",
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
            "description": "Creates new records in the specified model.",
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
                        "description": "Whether to return a download link to the PDF of the created document."
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
            "description": "Fetches records from the specified model based on the given criteria.",
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
                        "description": "A dictionary specifying the criteria for fetching records."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Specifies how many records to fetch."
                    },
                    "fields_option": {
                        "type": "string",
                        "description": "Specifies verbosity of records fetched."
                    },
                    "limited_fields": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of fields to fetch if fields_option is 'limited'."
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
            "description": "Updates an existing record in the specified model.",
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
            "description": "Deletes records in the specified model based on criteria.",
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
            "description": "Prints the specified record (subject to the record being printable).",
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
]