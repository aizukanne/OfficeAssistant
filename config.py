import os
import boto3
import openai
import weaviate
from weaviate.classes.init import Auth
from semantic_router.encoders import OpenAIEncoder
from slack_sdk import WebClient

# Initialize API keys from environment variables
calendar_id = os.getenv('GOOGLE_CALENDAR_ID')
cerebras_api_key = os.getenv('CEREBRAS_API_KEY')
gemini_api_key = os.getenv('GEMINI_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')
erpnext_api_key = os.getenv('ERPNEXT_API_KEY') 
erpnext_api_secret = os.getenv('ERPNEXT_API_SECRET') 
openai_api_key = os.getenv('OPENAI_API_KEY')
openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
slack_bot_token = os.getenv('SLACK_BOT_TOKEN')
telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
weaviate_api_key = os.getenv('WEAVIATE_API_KEY')
weaviate_url = os.getenv('WEAVIATE_URL')

# OpenAI headers
headers = {
    "X-OpenAI-Api-Key": openai_api_key,
}

# Odoo configuration
odoo_url = "http://167.71.140.93:8069"
odoo_db = "Production"
odoo_login = "ai_bot"
odoo_password = "Carbon123#"

# Initialize Slack client
slack_client = WebClient(token=slack_bot_token)

# Proxy configuration
proxy_url = "http://aizukanne3:Ng8qM7DCChitRRuGDusL_country-US,CA@core-residential.evomi.com:1000"

# User agents for web requests
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

# Initialize AWS services
dynamodb = boto3.resource('dynamodb')

# Initialize DynamoDB tables
names_table = dynamodb.Table('slack_usernames')
channels_table = dynamodb.Table('channels_table')
meetings_table = dynamodb.Table('meetings_table')

# Table names
assistant_table = 'AssistantMessages'
user_table = 'UserMessages'

# S3 Bucket names
image_bucket_name = 'mariaimagefolder-us'
docs_bucket_name = 'mariadocsfolder-us'

# Initialize OpenAI client
client = openai.OpenAI(
    api_key = os.getenv('OPENAI_API_KEY')
)

# Initialize OpenRouter client
openrouter_client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key = os.getenv('OPENROUTER_API_KEY')
)

# Initialize encoder
encoder = OpenAIEncoder(
    os.environ.get("OPENAI_API_KEY")
)

# Initialize Weaviate client
def get_weaviate_client():
    return weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key),
        headers=headers
    )

weaviate_client = get_weaviate_client()

# Default AI parameters
ai_temperature = 0.9