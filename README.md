# Office Assistant

A Slack-based AI assistant powered by OpenAI's GPT-4, capable of handling text, images, audio, and documents.

## Overview

Office Assistant is an AWS Lambda-based application that integrates with Slack to provide an intelligent assistant capable of:
- Processing natural language queries
- Analyzing images and documents
- Handling audio transcription and text-to-speech
- Performing web searches
- Managing user interactions and conversations
- Generating PDF reports

## Architecture

The application follows a modular architecture organized into the following components:

```
.
├── lambda_function.py           # AWS Lambda entry point
└── src/
    ├── handlers/               # Request handlers
    ├── clients/                # External API integrations
    ├── services/               # Business logic
    ├── data/                   # Data access layer
    ├── utils/                  # Utility functions
    └── core/                   # Core infrastructure
```

### Module Descriptions

- **handlers/**
  - `lambda_handler.py`: Main request handler for AWS Lambda events

- **clients/**
  - `openai_client.py`: OpenAI API integration for AI capabilities
  - `slack_client.py`: Slack API integration for messaging

- **services/**
  - `conversation_builder.py`: Manages conversation context and formatting
  - `message_processing.py`: Text analysis and message handling
  - `web_services.py`: Web browsing and search functionality
  - `audio_processing.py`: Audio file processing and conversion

- **data/**
  - `db_operations.py`: DynamoDB operations for message storage
  - `user_management.py`: User-related operations and caching
  - `channel_management.py`: Channel management and settings

- **utils/**
  - `file_operations.py`: File handling, PDF generation, S3 operations
  - `utils.py`: Shared utility functions

- **core/**
  - `config.py`: Configuration management
  - `error_handlers.py`: Error handling and logging
  - `middleware.py`: Request processing middleware

## Setup

### Prerequisites

- Python 3.11+
- AWS Account
- Slack Workspace with Bot Token
- OpenAI API Key

### AWS IAM Role Requirements

The Lambda function requires an IAM role with the following permissions:
- `AWSLambdaBasicExecutionRole` (for CloudWatch Logs)
- DynamoDB permissions:
  - Read/Write access to tables:
    - staff_history
    - maria_history
    - slack_usernames
    - channels_table
    - meetings_table
- S3 permissions:
  - Read/Write access to buckets:
    - mariaimagefolder-us
    - mariadocsfolder-us

### Environment Variables

```bash
# API Keys
SLACK_BOT_TOKEN=your-slack-bot-token
OPENAI_API_KEY=your-openai-api-key
GOOGLE_API_KEY=your-google-api-key
GEMINI_API_KEY=your-gemini-api-key

# External Services
CALENDAR_ID=your-google-calendar-id
ERPNEXT_API_KEY=your-erpnext-api-key
ERPNEXT_API_SECRET=your-erpnext-api-secret

# DynamoDB Tables
STAFF_HISTORY_TABLE=staff_history
MARIA_HISTORY_TABLE=maria_history
SLACK_USERNAMES_TABLE=slack_usernames
CHANNELS_TABLE=channels_table
MEETINGS_TABLE=meetings_table

# S3 Buckets
IMAGE_BUCKET=mariaimagefolder-us
DOCS_BUCKET=mariadocsfolder-us
```

### Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd office-assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Deploy to AWS Lambda:
```bash
# Using AWS SAM
sam build
sam deploy --guided

# Or using Serverless Framework
serverless deploy
```

## Features

### Message Processing
- Natural language understanding
- Context-aware conversations
- Message history tracking
- Thread support

### File Handling
- Image analysis and processing
- Document parsing (PDF, DOCX, CSV, XLSX)
- File conversion and formatting
- S3 storage integration

### Audio Processing
- Speech-to-text transcription
- Text-to-speech conversion
- Audio file format conversion
- Multi-file processing

### Web Integration
- Web page scraping
- Google search integration
- URL processing
- Content summarization

### User Management
- User profile caching
- Channel management
- Mute/unmute functionality
- Permission handling

## API Endpoints

The Lambda function handles various event types:

### Slack Events
- `app_mention`: Handles direct mentions
- `message`: Processes channel messages
- `file_shared`: Handles file uploads

### Email Events
- Processes incoming emails
- Extracts content and attachments
- Generates appropriate responses

## Error Handling

The application implements comprehensive error handling:
- Request validation
- Rate limiting
- Error logging
- Graceful degradation
- User-friendly error messages

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
The project follows PEP 8 guidelines. Run linting with:
```bash
flake8 src/
```

### Contributing
Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Dependencies

Main dependencies include:
- `openai`: OpenAI API client
- `boto3`: AWS SDK for Python
- `aiohttp`: Async HTTP client/server
- `nltk`: Natural language processing
- `PyPDF2`: PDF processing
- `python-docx`: Word document processing
- `markdown2`: Markdown processing
- `fpdf`: PDF generation

## License

MIT License - See [LICENSE](LICENSE) file for details