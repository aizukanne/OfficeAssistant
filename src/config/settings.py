import os
from typing import Dict, Any, Optional, List

# API Keys and Authentication
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GOOGLE_API_KEY = os.getenv('CUSTOM_SEARCH_API_KEY')  # Updated to match env var
GOOGLE_SEARCH_CX = os.getenv('CUSTOM_SEARCH_ID')     # Updated to match env var
OPENWEATHER_KEY = os.getenv('OPENWEATHER_KEY')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')         # Added
ERPNEXT_API_KEY = os.getenv('ERPNEXT_API_KEY')       # Added
ERPNEXT_API_SECRET = os.getenv('ERPNEXT_API_SECRET') # Added

# Calendar Configuration
CALENDAR_ID = os.getenv('CALENDAR_ID')
CALENDAR_TOKEN = os.getenv('CALENDAR_TOKEN')
CALENDAR_CREDENTIALS = os.getenv('CALENDAR_CREDENTIALS')

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
PROXY_URL = os.getenv('PROXY_URL', '')  # Added direct export
PROXY_CONFIG = {
    'url': PROXY_URL,
    'enabled': bool(os.getenv('PROXY_ENABLED', False))
}

# NLTK Configuration
NLTK_DATA_PATH = "/opt/python/nltk_data"  # Added direct export
NLTK_CONFIG = {
    'data_path': NLTK_DATA_PATH,
    'required_packages': ['punkt', 'stopwords']  # Only these packages are used in the codebase
}

# OpenAI Configuration
OPENAI_MODELS = {  # Added
    'default': 'gpt-4',
    'vision': 'gpt-4-vision-preview',
    'embedding': 'text-embedding-ada-002'
}
OPENAI_MAX_TOKENS = 2000  # Added
OPENAI_TEMPERATURE = 0.7  # Added

# Text Processing Configuration
TEXT_PROCESSING = {
    'max_summary_sentences': 50,
    'max_full_text_sentences': 150,
    'max_sentence_words': 30
}

# File Processing Configuration
FILE_SIZE_LIMIT_MB = 10  # Added
ALLOWED_FILE_TYPES = [    # Added
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/pdf',
    'text/plain',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
]

# Message Retention
MESSAGE_TTL_DAYS = 20  # Added

# Default Channel IDs
DEFAULT_CHANNELS = {  # Added
    'general': os.getenv('DEFAULT_CHANNEL_GENERAL', ''),
    'notifications': os.getenv('DEFAULT_CHANNEL_NOTIFICATIONS', ''),
    'email_notifications': os.getenv('DEFAULT_CHANNEL_EMAIL', ''),
    'default_user': os.getenv('DEFAULT_USER_ID', '')
}

# AWS Configuration
AWS_CONFIG = {
    'region': os.getenv('AWS_REGION', 'us-east-1'),
    'access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
    'secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY')
}

# Odoo Configuration
ODOO_URL = os.getenv('ODOO_URL')        # Added direct export
ODOO_DB = os.getenv('ODOO_DB')          # Added direct export
ODOO_LOGIN = os.getenv('ODOO_USERNAME')  # Added direct export
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD')  # Added direct export
ODOO_CONFIG = {
    'url': ODOO_URL,
    'db': ODOO_DB,
    'username': ODOO_LOGIN,
    'password': ODOO_PASSWORD
}

def get_env(key: str, default: Any = None) -> Any:
    """Get environment variable with default."""
    return os.getenv(key, default)

def validate_settings() -> Dict[str, str]:
    """Validate all settings."""
    missing = {}
    
    # Check required API keys
    if not OPENAI_API_KEY:
        missing['OPENAI_API_KEY'] = "OpenAI API key is required"
    if not GOOGLE_API_KEY:
        missing['CUSTOM_SEARCH_API_KEY'] = "Google Custom Search API key is required"
    if not GOOGLE_SEARCH_CX:
        missing['CUSTOM_SEARCH_ID'] = "Google Custom Search ID is required"
    if not OPENWEATHER_KEY:
        missing['OPENWEATHER_KEY'] = "OpenWeather API key is required"
    if not SLACK_BOT_TOKEN:
        missing['SLACK_BOT_TOKEN'] = "Slack bot token is required"
    
    # Check calendar configuration
    if not CALENDAR_ID:
        missing['CALENDAR_ID'] = "Calendar ID is required"
    if not CALENDAR_TOKEN:
        missing['CALENDAR_TOKEN'] = "Calendar token is required"
    if not CALENDAR_CREDENTIALS:
        missing['CALENDAR_CREDENTIALS'] = "Calendar credentials are required"
        
    # Check AWS configuration
    if not AWS_CONFIG['access_key_id']:
        missing['AWS_ACCESS_KEY_ID'] = "AWS access key ID is required"
    if not AWS_CONFIG['secret_access_key']:
        missing['AWS_SECRET_ACCESS_KEY'] = "AWS secret access key is required"
        
    # Check Odoo configuration
    if not ODOO_URL:
        missing['ODOO_URL'] = "Odoo URL is required"
    if not ODOO_DB:
        missing['ODOO_DB'] = "Odoo database name is required"
    if not ODOO_LOGIN:
        missing['ODOO_USERNAME'] = "Odoo username is required"
    if not ODOO_PASSWORD:
        missing['ODOO_PASSWORD'] = "Odoo password is required"
        
    return missing

def get_table_name(table: str) -> str:
    """Get DynamoDB table name."""
    return DYNAMODB_TABLES.get(table, '')

def get_bucket_name(bucket: str) -> str:
    """Get S3 bucket name."""
    return S3_BUCKETS.get(bucket, '')

def get_allowed_file_types() -> List[str]:
    """Get allowed file types."""
    return ALLOWED_FILE_TYPES

def get_openai_model(model_type: str = 'default') -> str:
    """Get OpenAI model name."""
    return OPENAI_MODELS.get(model_type, OPENAI_MODELS['default'])

def get_default_channel(channel_type: str = 'general') -> str:
    """Get default channel ID."""
    return DEFAULT_CHANNELS.get(channel_type, '')

def get_proxy_url() -> str:
    """Get proxy URL if enabled."""
    return PROXY_URL if PROXY_CONFIG['enabled'] else ''

def get_user_agent() -> str:
    """Get random user agent."""
    from random import choice
    return choice(USER_AGENTS)

def get_api_endpoint(service: str, endpoint: str) -> str:
    """Get API endpoint URL."""
    return API_ENDPOINTS.get(service, {}).get(endpoint, '')