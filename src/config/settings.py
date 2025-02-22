import os
from typing import Dict, Optional

# API Keys and Authentication
SLACK_BOT_TOKEN: str = os.getenv('SLACK_BOT_TOKEN', '')
GOOGLE_API_KEY: str = os.getenv('GOOGLE_API_KEY', '')
GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
CALENDAR_ID: str = os.getenv('GOOGLE_CALENDAR_ID', '')
ERPNEXT_API_KEY: str = os.getenv('ERPNEXT_API_KEY', '')
ERPNEXT_API_SECRET: str = os.getenv('ERPNEXT_API_SECRET', '')
OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
OPENWEATHER_KEY: str = os.getenv('OPENWEATHER_KEY', '')

# Odoo Configuration
ODOO_URL: str = os.getenv('ODOO_URL', '')
ODOO_DB: str = os.getenv('ODOO_DB', '')
ODOO_LOGIN: str = os.getenv('ODOO_LOGIN', '')
ODOO_PASSWORD: str = os.getenv('ODOO_PASSWORD', '')

# DynamoDB Tables
DYNAMODB_TABLES: Dict[str, str] = {
    'user': 'staff_history',
    'assistant': 'maria_history',
    'names': 'slack_usernames',
    'channels': 'channels_table',
    'meetings': 'meetings_table'
}

# S3 Buckets
S3_BUCKETS: Dict[str, str] = {
    'images': 'mariaimagefolder-us',
    'docs': 'mariadocsfolder-us'
}

# NLTK Configuration
NLTK_DATA_PATH: str = "/opt/python/nltk_data"

# OpenAI Configuration
OPENAI_MODELS: Dict[str, str] = {
    'default': 'gpt-4o-2024-11-20',
    'audio': 'gpt-4o-audio-preview-2024-12-17',
    'embeddings': 'text-embedding-ada-002'
}

OPENAI_MAX_TOKENS: int = 5500
OPENAI_TEMPERATURE: float = 0.9

# File Processing
FILE_SIZE_LIMIT_MB: int = 5
ALLOWED_FILE_TYPES: Dict[str, list] = {
    'images': ['.jpg', '.jpeg', '.png', '.gif'],
    'documents': ['.pdf', '.docx', '.txt', '.md'],
    'audio': ['.mp3', '.wav', '.m4a']
}

# Proxy Configuration
PROXY_URL: str = "http://aizukanne3:Ng8qM7DCChitRRuGDusL_country-US,CA@core-residential.evomi.com:1000"

# Message Retention
MESSAGE_TTL_DAYS: int = 20

# Default Channel IDs
DEFAULT_CHANNELS: Dict[str, str] = {
    'email_notifications': 'C06QL84KZGQ',
    'default_user': 'U02RPR2RMJS'
}

def get_env(key: str, default: Optional[str] = None) -> str:
    """
    Get environment variable with a default value.
    
    Args:
        key: Environment variable key
        default: Default value if key not found
        
    Returns:
        str: Environment variable value or default
    """
    return os.getenv(key, default or '')

def validate_settings() -> bool:
    """
    Validate that all required settings are present.
    
    Returns:
        bool: True if all required settings are present
    """
    required_settings = [
        SLACK_BOT_TOKEN,
        OPENAI_API_KEY,
        ODOO_URL,
        ODOO_DB,
        ODOO_LOGIN,
        ODOO_PASSWORD
    ]
    
    return all(required_settings)

def get_dynamodb_table(table_key: str) -> str:
    """
    Get DynamoDB table name by key.
    
    Args:
        table_key: Key in DYNAMODB_TABLES dictionary
        
    Returns:
        str: Table name
    """
    return DYNAMODB_TABLES.get(table_key, '')

def get_s3_bucket(bucket_key: str) -> str:
    """
    Get S3 bucket name by key.
    
    Args:
        bucket_key: Key in S3_BUCKETS dictionary
        
    Returns:
        str: Bucket name
    """
    return S3_BUCKETS.get(bucket_key, '')

def get_allowed_file_types(category: str) -> list:
    """
    Get allowed file types for a category.
    
    Args:
        category: Category in ALLOWED_FILE_TYPES dictionary
        
    Returns:
        list: List of allowed file extensions
    """
    return ALLOWED_FILE_TYPES.get(category, [])

def get_openai_model(model_key: str = 'default') -> str:
    """
    Get OpenAI model name by key.
    
    Args:
        model_key: Key in OPENAI_MODELS dictionary
        
    Returns:
        str: Model name
    """
    return OPENAI_MODELS.get(model_key, OPENAI_MODELS['default'])

def get_default_channel(channel_key: str) -> str:
    """
    Get default channel ID by key.
    
    Args:
        channel_key: Key in DEFAULT_CHANNELS dictionary
        
    Returns:
        str: Channel ID
    """
    return DEFAULT_CHANNELS.get(channel_key, '')