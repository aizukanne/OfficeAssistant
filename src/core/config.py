import os
import boto3
from tools import tools  # Import tools from tools.py

# API Keys and Tokens
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID')
ERPNEXT_API_KEY = os.getenv('ERPNEXT_API_KEY')
ERPNEXT_API_SECRET = os.getenv('ERPNEXT_API_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# ERPNext Configuration
ODOO_URL = os.getenv('ODOO_URL')
ODOO_DB = os.getenv('ODOO_DB')
ODOO_LOGIN = os.getenv('ODOO_LOGIN')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD')

# Proxy Configuration
PROXY_URL = os.getenv('PROXY_URL')

# AWS Resources
dynamodb = boto3.resource('dynamodb')

# DynamoDB Tables
USER_TABLE = dynamodb.Table(os.getenv('STAFF_HISTORY_TABLE', 'staff_history'))
ASSISTANT_TABLE = dynamodb.Table(os.getenv('MARIA_HISTORY_TABLE', 'maria_history'))
NAMES_TABLE = dynamodb.Table(os.getenv('SLACK_USERNAMES_TABLE', 'slack_usernames'))
CHANNELS_TABLE = dynamodb.Table(os.getenv('CHANNELS_TABLE', 'channels_table'))
MEETINGS_TABLE = dynamodb.Table(os.getenv('MEETINGS_TABLE', 'meetings_table'))

# S3 Buckets
IMAGE_BUCKET_NAME = os.getenv('IMAGE_BUCKET', 'mariaimagefolder-us')
DOCS_BUCKET_NAME = os.getenv('DOCS_BUCKET', 'mariadocsfolder-us')

# OpenAI Configuration
AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.9'))
OPENAI_TOOLS = tools

# User Agents for Web Requests
USER_AGENTS = [
    # Chrome (Windows, macOS, Linux)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",

    # Firefox (Windows, macOS, Linux)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:93.0) Gecko/20100101 Firefox/93.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",

    # Safari (macOS, iOS)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.1.2 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",

    # Edge (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.64",

    # Opera
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.277",

    # Mobile Browsers (Android, iOS)
    "Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Pixel 4 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1"
]

# NLTK Configuration
NLTK_DATA_PATH = os.getenv('NLTK_DATA', "/opt/python/nltk_data")

# Default Values
DEFAULT_MAX_SENTENCES = int(os.getenv('DEFAULT_MAX_SENTENCES', '10'))
DEFAULT_SUMMARY_LENGTH = int(os.getenv('DEFAULT_SUMMARY_LENGTH', '5'))
DEFAULT_FILE_SIZE_LIMIT_MB = int(os.getenv('DEFAULT_FILE_SIZE_LIMIT_MB', '5'))

# API Endpoints
SLACK_API_BASE = "https://slack.com/api"
OPENAI_API_BASE = "https://api.openai.com/v1"
GOOGLE_SEARCH_API = "https://www.googleapis.com/customsearch/v1"

# Error Messages
ERROR_MESSAGES = {
    "no_user_id": "No user ID found. Stopping execution.",
    "bot_message": "Ignored message from bot",
    "file_size_limit": lambda size: f"File is over the {size} MB limit.",
    "unsupported_file": "Unsupported file type",
    "api_error": lambda e: f"An error occurred during the API call: {e}",
    "download_error": lambda e: f"Error downloading file: {e}",
    "process_error": lambda e: f"Error processing file: {e}"
}

# Function Configuration
FUNCTION_DEFAULTS = {
    "max_tokens": int(os.getenv('MAX_TOKENS', '5500')),
    "default_model": os.getenv('DEFAULT_MODEL', 'gpt-4o-2024-11-20'),
    "audio_model": os.getenv('AUDIO_MODEL', 'gpt-4o-audio-preview-2024-12-17'),
    "embedding_model": os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002'),
    "tts_model": os.getenv('TTS_MODEL', 'tts-1'),
    "tts_voice": os.getenv('TTS_VOICE', 'shimmer'),
    "whisper_model": os.getenv('WHISPER_MODEL', 'whisper-1')
}