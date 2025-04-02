# Configuration

[← Back to Main](README.md) | [Prompt Configuration](prompt-configuration.md) | [Invocation Flow →](invocation-flow.md)

The configuration of the Maria AI Assistant system is managed through the `config.py` file, which contains environment variables, service connections, and system settings.

## Overview

The configuration module provides:

- API keys and credentials
- Database connection settings
- Service endpoints
- System parameters
- Environment-specific settings

## Configuration Structure

The `config.py` file is organized into several sections:

### API Keys

```python
# OpenAI API configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_ORG_ID = os.environ.get("OPENAI_ORG_ID")

# Slack API configuration
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

# AWS configuration
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
```

### Database Connections

```python
# DynamoDB configuration
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "maria-messages")
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT")

# Weaviate configuration
WEAVIATE_URL = os.environ.get("WEAVIATE_URL")
WEAVIATE_API_KEY = os.environ.get("WEAVIATE_API_KEY")
```

### Service URLs

```python
# ERP system URLs
ERPNEXT_URL = os.environ.get("ERPNEXT_URL")
ODOO_URL = os.environ.get("ODOO_URL")

# External service URLs
WEATHER_API_URL = os.environ.get("WEATHER_API_URL")
GOOGLE_SEARCH_URL = os.environ.get("GOOGLE_SEARCH_URL")
```

### System Parameters

```python
# System settings
DEBUG_MODE = os.environ.get("DEBUG_MODE", "False").lower() == "true"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "4000"))
```

## Environment Variables

The system relies on environment variables for configuration, which can be set in several ways:

1. In the AWS Lambda environment
2. In a local `.env` file for development
3. Through environment variable injection in CI/CD pipelines
4. Via AWS Parameter Store or Secrets Manager

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | API key for OpenAI services | `sk-...` |
| `SLACK_BOT_TOKEN` | Bot token for Slack API | `xoxb-...` |
| `SLACK_SIGNING_SECRET` | Signing secret for Slack API | `...` |
| `DYNAMODB_TABLE` | DynamoDB table name | `maria-messages` |
| `WEAVIATE_URL` | URL for Weaviate instance | `https://...` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region | `us-east-1` |
| `DEBUG_MODE` | Enable debug mode | `False` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_TOKENS` | Maximum tokens for OpenAI | `4000` |

## Service Connections

The configuration includes settings for connecting to various services:

### OpenAI

```python
# OpenAI client configuration
openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    organization=OPENAI_ORG_ID
)
```

### AWS Services

```python
# AWS service clients
dynamodb = boto3.resource(
    'dynamodb',
    region_name=AWS_REGION,
    endpoint_url=DYNAMODB_ENDPOINT
)

s3 = boto3.client(
    's3',
    region_name=AWS_REGION
)
```

### Weaviate

```python
# Weaviate client configuration
weaviate_client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY)
)
```

## Proxy Settings

For environments that require proxy access:

```python
# Proxy configuration
HTTP_PROXY = os.environ.get("HTTP_PROXY")
HTTPS_PROXY = os.environ.get("HTTPS_PROXY")
NO_PROXY = os.environ.get("NO_PROXY")

proxies = {
    "http": HTTP_PROXY,
    "https": HTTPS_PROXY
}
```

## User Agents

A list of user agents for web requests:

```python
# User agents for web requests
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    # Additional user agents...
]
```

## Configuration Loading

The configuration is loaded when the module is imported:

```python
def load_config():
    """Load configuration from environment variables and initialize clients"""
    # Load environment variables from .env file if it exists (development only)
    if os.path.exists(".env"):
        from dotenv import load_dotenv
        load_dotenv()
    
    # Initialize clients
    initialize_clients()
    
    return {
        "openai_client": openai_client,
        "dynamodb": dynamodb,
        "s3": s3,
        "weaviate_client": weaviate_client
    }

# Load configuration
config = load_config()
```

## Environment-Specific Configuration

The system supports different configurations for different environments:

```python
# Environment-specific settings
ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")

if ENVIRONMENT == "development":
    # Development settings
    DEBUG_MODE = True
    LOG_LEVEL = "DEBUG"
    
elif ENVIRONMENT == "testing":
    # Testing settings
    DYNAMODB_TABLE = "maria-messages-test"
    
elif ENVIRONMENT == "production":
    # Production settings
    DEBUG_MODE = False
    LOG_LEVEL = "WARNING"
```

## Customizing Configuration

To customize the configuration:

1. Modify environment variables in the deployment environment
2. Update the `config.py` file with new settings
3. Add new configuration sections as needed
4. Create environment-specific configuration overrides

## Best Practices

When working with the configuration:

- Store sensitive information in secure locations (AWS Secrets Manager, environment variables)
- Use meaningful default values where appropriate
- Document all configuration options
- Validate configuration values on startup
- Use environment-specific configurations for different stages

## Implementation Details

The configuration module is implemented in `config.py`:

```python
import os
import boto3
import weaviate
from openai import OpenAI

# Load environment variables
# API keys and credentials
# Database connections
# Service URLs
# System parameters

# Initialize clients
# OpenAI client
# AWS services
# Weaviate client

# Export configuration
config = {
    "openai_client": openai_client,
    "dynamodb": dynamodb,
    "s3": s3,
    "weaviate_client": weaviate_client,
    # Additional configuration...
}
```

This configuration is imported and used throughout the system to connect to services and control behavior.

---

[← Back to Main](README.md) | [Prompt Configuration](prompt-configuration.md) | [Invocation Flow →](invocation-flow.md)