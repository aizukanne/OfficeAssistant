import os
from typing import Dict, Any

# API Keys and Credentials
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_SEARCH_CX = os.getenv('GOOGLE_SEARCH_CX')
OPENWEATHER_KEY = os.getenv('OPENWEATHER_KEY')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')

# S3 Configuration
S3_BUCKETS = {
    'images': 'mariaimagefolder-us',
    'documents': 'mariadocsfolder-us'
}

# DynamoDB Tables
DYNAMODB_TABLES = {
    'user': 'staff_history',
    'assistant': 'maria_history',
    'usernames': 'slack_usernames',
    'channels': 'channels_table',
    'meetings': 'meetings_table'
}

# API Endpoints
API_ENDPOINTS = {
    'openweather': {
        'geo': 'http://api.openweathermap.org/geo/1.0/direct',
        'weather': 'https://api.openweathermap.org/data/3.0/onecall'
    },
    'google': {
        'calendar': 'https://www.googleapis.com/calendar/v3/calendars',
        'search': 'https://www.googleapis.com/customsearch/v1',
        'oauth': 'https://oauth2.googleapis.com/token'
    },
    'slack': {
        'message': 'https://slack.com/api/chat.postMessage',
        'upload': 'https://slack.com/api/files.upload',
        'users': 'https://slack.com/api/users.info',
        'conversations': 'https://slack.com/api/conversations.list'
    }
}

# HTTP Configuration
HTTP_CONFIG = {
    'timeout': 30,
    'max_retries': 3,
    'retry_delay': 1,  # seconds
    'max_concurrent_requests': 5
}

# Proxy Configuration
PROXY_CONFIG = {
    'url': "http://aizukanne3:Ng8qM7DCChitRRuGDusL_country-US,CA@core-residential.evomi.com:1000",
    'enabled': True
}

# User Agents
USER_AGENTS = [
    # Chrome (Windows, macOS, Linux)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
    # Firefox (Windows, macOS, Linux)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:93.0) Gecko/20100101 Firefox/93.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0"
]

# NLTK Configuration
NLTK_CONFIG = {
    'data_path': "/opt/python/nltk_data",
    'required_packages': ['punkt', 'stopwords', 'averaged_perceptron_tagger']
}

# Text Processing Configuration
TEXT_PROCESSING = {
    'max_summary_sentences': 50,
    'max_full_text_sentences': 150,
    'max_sentence_words': 30
}

def validate_config() -> Dict[str, Any]:
    """
    Validates the configuration and returns any missing required settings.
    
    Returns:
        Dict[str, Any]: Dictionary of missing settings and their descriptions
    """
    missing = {}
    
    # Check required API keys
    if not OPENAI_API_KEY:
        missing['OPENAI_API_KEY'] = "OpenAI API key is required"
    if not GOOGLE_API_KEY:
        missing['GOOGLE_API_KEY'] = "Google API key is required"
    if not GOOGLE_SEARCH_CX:
        missing['GOOGLE_SEARCH_CX'] = "Google Search CX is required"
    if not OPENWEATHER_KEY:
        missing['OPENWEATHER_KEY'] = "OpenWeather API key is required"
    if not SLACK_BOT_TOKEN:
        missing['SLACK_BOT_TOKEN'] = "Slack bot token is required"
        
    return missing

def get_proxy_url() -> str:
    """
    Returns the proxy URL if proxy is enabled.
    
    Returns:
        str: Proxy URL if enabled, empty string otherwise
    """
    return PROXY_CONFIG['url'] if PROXY_CONFIG['enabled'] else ''

def get_user_agent() -> str:
    """
    Returns a random user agent from the list.
    
    Returns:
        str: Random user agent string
    """
    from random import choice
    return choice(USER_AGENTS)

def get_api_endpoint(service: str, endpoint: str) -> str:
    """
    Gets the API endpoint URL for a specific service and endpoint.
    
    Args:
        service: Service name (e.g., 'openweather', 'google', 'slack')
        endpoint: Endpoint name (e.g., 'geo', 'weather', 'calendar')
        
    Returns:
        str: API endpoint URL
    """
    return API_ENDPOINTS.get(service, {}).get(endpoint, '')

def get_table_name(table: str) -> str:
    """
    Gets the DynamoDB table name.
    
    Args:
        table: Table identifier (e.g., 'user', 'assistant', 'usernames')
        
    Returns:
        str: DynamoDB table name
    """
    return DYNAMODB_TABLES.get(table, '')

def get_bucket_name(bucket: str) -> str:
    """
    Gets the S3 bucket name.
    
    Args:
        bucket: Bucket identifier (e.g., 'images', 'documents')
        
    Returns:
        str: S3 bucket name
    """
    return S3_BUCKETS.get(bucket, '')