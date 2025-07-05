tools = [
    {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": "Performs a Google search and retrieves web content for the top five results. Use search operators in the search string to enhance the quality and relevance of the results. The function constructs a search query that incorporates various modifiers such as date ranges and specific text occurrences, and retrieves web content including text and images for the first five results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "The primary term to search for. Can be combined with operators to refine search results."
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
            "description": "Extracts and refines web content from a list of URLs, offering the option to retrieve either the full text or a summary of each article. The function utilizes the BeautifulSoup library to parse and analyze web articles for text and relevant images, making it suitable for aggregating and processing web content for data analysis or content curation. It also provides a list of internal URLs found within the page. Users can specify whether to return the full text or a summary of the content through the 'full_text' parameter, enhancing its flexibility for various use cases.",
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
            "description": "Retrieves the details of a specific message from a DynamoDB table based on its sort key identifier. This function is particularly useful for recalling the details of a previously discussed topic or conversation, allowing the AI chat bot to access and remember past message contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "description": "The role of the entity that sent the message, either user or assistant."
                    },
                    "sort_id": {
                        "type": "number",
                        "description": "The unique sort key identifier of the message to retrieve. It corresponds to a specific message in the chat history."
                    },
                    "chat_id": {
                        "type": "string",
                        "description": "The unique chat key identifier of the message to retrieve. It corresponds to a group of messages in the chat history."
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
            "description": "Retrieves the summary of a range of messages from a DynamoDB table based on the sort key range provided. This function is beneficial for extracting a sequence of messages within a specific time frame, enabling the AI chat bot to analyze or recap conversations over a given period. ",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "The unique chat identifier. Used to identify the specific conversation thread from which to retrieve the messages." 
                    },
                    "start_sort_id": {
                        "type": "number",
                        "description": "The starting point of the sort key range. It is a Unix timestamp marking the beginning of the message retrieval range."
                    },
                    "end_sort_id": {
                        "type": "number",
                        "description": "The ending point of the sort key range. It is a Unix timestamp marking the end of the message retrieval range." 
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
            "description": "Processes a given text string to clean it up and then generates an embedding using OpenAI's embedding model. This function is ideal for converting text into a numerical representation that captures its semantic meaning. It's useful in scenarios where text data needs to be analyzed or compared in a more quantifiable format, such as in machine learning models or data analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text string to be processed and converted into an embedding. The function cleans the text by replacing newline characters with spaces."
                    },
                    "model": {
                        "type": "string",
                        "default": "text-embedding-ada-002",
                        "description": "The specific OpenAI embedding model to use for generating the text embedding. Defaults to 'text-embedding-ada-002' if not specified."  
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
            "description": "Relays a message to a Slack user based on their real name or display name. If multiple or similar names are found, it provides options for clarification. Always provide the message in the format {user} has asked me to inform you...., where user is the name of the user on whose behalf you are sending the message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to be sent to the user."
                    },
                    "channel": {
                        "type": "string",
                        "description": "The user_id or channel_id of the user to send the message to and not the user's name or display name. You can get this from the get_users function."
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
            "description": "Returns a list of all users with their user_id, display_name and email. Each user_id is the channel for the user.",
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
            "description": "Sends a response to the user as an audio message. The text provided is converted to audio using a text_to_speech function and transmitted to the user. Use this when a user requests a verbal response.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "The ID of the Slack channel where the file will be uploaded."
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to be converted to speech and uploaded as an audio file. When generating the text, always include umms, errs and ahhs in the text to mimic natural human speech patterns.  "
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
            "description": "Sends a file to a specified Slack channel or user. The file can be of any type, and it can optionally be uploaded as a reply in a thread.",
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
            "description": "Converts formatted text to a beautiful, professional PDF with enhanced styling and uploads it to a specified Slack channel. The text can contain Markdown formatting and images, which will be rendered with professional typography, color schemes, and layout. Supports multiple themes and advanced formatting features including images from URLs, local files, or base64 data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to be converted to PDF, which may contain Markdown formatting including headers, lists, bold/italic text, images, tables, and other markdown features. Images can be included using standard markdown syntax with URLs, local paths, or base64 data."
                    },
                    "chat_id": {
                        "type": "string",
                        "description": "The ID of the Slack channel where the PDF will be uploaded."
                    },
                    "title": {
                        "type": "string",
                        "description": "The title of the PDF file to be uploaded. This will appear in headers and as the document title."
                    },
                    "ts": {
                        "type": "string",
                        "description": "Optional. The thread timestamp (ts) to reply in a thread."
                    },
                    "theme": {
                        "type": "string",
                        "description": "Optional. The visual theme for the PDF styling. Options: 'professional' (default - blue/gray corporate theme), 'modern' (black/red contemporary theme), or 'corporate' (navy/blue traditional theme).",
                        "enum": ["professional", "modern", "corporate"],
                        "default": "professional"
                    },
                    "include_title_page": {
                        "type": "boolean",
                        "description": "Optional. Whether to include a decorative title page at the beginning of the PDF. Default is false."
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
            "description": "Lists the files available on the system. Returns a dictionary where each key is the file name and the value is the object URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_prefix": {
                        "type": "string",
                        "description": "Optional. The name of the folder whose files you want to list. Should end with a slash ('/') if provided."
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
            "description": "Retrieves a list of all slack channels on this slack workspace. The list provides detailed information on each channel.",
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
            "description": "Sends a text prompt to the Openai o1 advanced reasoning LLM API and retrieves the generated content. It's designed to interact with OpenAI's Generative Language API to produce creative and solutions to challenges provided as text descriptions on the input prompt, making it suitable for applications such as problem solving, advanced reasoning challenges, plan development, and other complex natural language processing tasks.",
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
            "description": "Sets or checks the mute status for the chat. If a status is provided, it sets the mute status to the given value and returns the new status. If no status is provided, it checks and returns the current mute status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": ["boolean", "null"],
                        "description": "The boolean value to set for the 'maria_status' attribute. Must be either True or False. If not provided, the current mute status will be checked."
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
                        "description": "A dictionary of parameters that the code may require. Each key-value pair in this dictionary will be available as a variable in the executed code."
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "odoo_get_mapped_models",
            "description": "Fetches all available mapped models and optionally fields for each model from the Odoo API. This function retrieves information about mapped models, optionally including their field mappings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_fields": {
                        "type": "boolean",
                        "description": "Whether to include field mappings in the response. Defaults to True."
                    },
                    "model_name": {
                        "type": ["string", "null"],
                        "description": "Optional filter to retrieve information for a specific model only. It can be the name or synonym for the model in question. For example, for customers, partners, customers, clients etc can be used. Defaults to None."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "odoo_create_record",
            "description": "Creates a new record in the specified external model through an API. This function first authenticates with the Odoo instance using global credentials and then sends a POST request to create a new record with the provided data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "external_model": {
                        "type": "string",
                        "description": "The name of the external model where the record will be created."
                    },
                    "record_data": {
                        "type": "object",
                        "description": "A json object containing the details for the new record. The keys should correspond to field names in the external model. For example, to create a customer use fields from the model to generate a record_data object like this {'full_name': 'Customer 218', 'contact_email': 'customer218@gmail.com', 'is_customer': 1}. this must be provided as a json object."
                    }
                },
                "required": ["external_model", "record_data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "odoo_fetch_records",
            "description": "Retrieves records from an external model through the Odoo API. This function first authenticates with the Odoo instance using global credentials and then sends a request to fetch records based on optional filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "external_model": {
                        "type": "string",
                        "description": "The name of the external model to fetch records from."
                    },
                    "filters": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "array",
                            "items": {
                                "type": ["string", "number", "boolean", "null"]
                            }
                        },
                        "description": "Optional Odoo domain filters to narrow down the records to fetch. It is an array of arrays, where each sub-array consists of filter conditions. Defaults to None."
                    }
                },
                "required": ["external_model"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "odoo_update_record",
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
            "name": "odoo_delete_record",
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
            "name": "odoo_print_record",
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
    }, 
    {
        "type": "function",
        "function": {
            "name": "odoo_post_record",
            "description": "Posts a record in the specified model using the record ID. This function handles authentication and then sends a PUT request to the Odoo API to post the record.",
            "parameters": {
                "type": "object",
                "properties": {
                    "external_model": {
                        "type": "string",
                        "description": "The technical name of the external model."
                    },
                    "record_id": {
                        "type": "integer",
                        "description": "The ID of the record to post."
                    }
                },
                "required": ["external_model", "record_id"]
            }
        }
    },           
    {
        "type": "function",
        "function": {
            "name": "search_and_format_products",
            "description": "Searches for products on Amazon via the Real-Time Amazon Data API and returns formatted results. The function handles API request parameters, makes the HTTP request to Amazon's search endpoint, and processes the response data into a readable format. It supports various filtering options including country selection, sorting preferences, product condition, Prime eligibility, and deals filtering. The function is particularly useful for e-commerce applications, price comparison tools, and product research, providing a convenient way to access structured Amazon product data programmatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search term to query Amazon with, such as product name, brand, or category."
                    },
                    "country": {
                        "type": "string",
                        "description": "The Amazon marketplace country code (e.g., 'US', 'CA', 'UK'). Default is 'CA'."
                    },
                    "max_products": {
                        "type": "integer",
                        "description": "Maximum number of products to show in the formatted results. Default is 5."
                    },
                    "page": {
                        "type": "integer",
                        "description": "The page number of search results to retrieve. Default is 1."
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "How to sort the results. Options include 'RELEVANCE', 'PRICE_LOW_TO_HIGH', 'PRICE_HIGH_TO_LOW', 'RATING', 'NEWEST'. Default is 'RELEVANCE'."
                    },
                    "product_condition": {
                        "type": "string",
                        "description": "Filter for product condition. Options include 'NEW', 'USED', 'REFURBISHED'. Default is 'NEW'."
                    },
                    "is_prime": {
                        "type": "boolean",
                        "description": "Filter for Amazon Prime eligible products. Default is False."
                    },
                    "deals_and_discounts": {
                        "type": "string",
                        "description": "Filter for deals and discounts. Options include 'NONE', 'TODAY_DEALS', 'ON_SALE'. Default is 'NONE'."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_slack_channel_description",
            "description": "Sets the purpose (description) and/or topic of a Slack channel. Can update either or both properties. Supports both channel IDs and channel names with automatic resolution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "The channel ID (e.g., 'C1234567890') or channel name (e.g., 'general', '#general'). Channel names will be automatically resolved to IDs."
                    },
                    "purpose": {
                        "type": "string",
                        "description": "Optional. The new purpose/description for the channel. This appears in the channel info and describes what the channel is for."
                    },
                    "topic": {
                        "type": "string",
                        "description": "Optional. The new topic for the channel. This appears at the top of the channel and is typically used for current discussions or announcements."
                    }
                },
                "required": ["channel"]
            }
        }
    }
]
