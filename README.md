# Office Assistant

A Lambda-based AI assistant that integrates with Slack, Odoo ERP, and various external services to help with office tasks.

## Project Structure

```
OfficeAssistantRefactored/
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── prompts.py        # AI assistant prompts and instructions
│   │   └── settings.py       # Configuration and environment variables
│   ├── handlers/
│   │   ├── __init__.py
│   │   └── message_handler.py # Message processing functions
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py   # Authentication services
│   │   ├── external_services.py # External API integrations
│   │   ├── odoo_service.py   # Odoo ERP integration
│   │   ├── openai_service.py # OpenAI API integration
│   │   ├── slack_service.py  # Slack API integration
│   │   └── storage_service.py # DynamoDB and S3 operations
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_processing.py # File handling utilities
│   │   ├── text_processing.py # Text processing utilities
│   │   └── tools.py          # Tool definitions and utilities
│   └── __init__.py
├── lambda_function.py        # Main Lambda handler
└── README.md                 # Project documentation
```

## Features

- Slack Integration
  - Message handling
  - File uploads/downloads
  - Audio message support
  - Channel management
  - User management

- Odoo ERP Integration
  - Model access
  - Record operations (CRUD)
  - Field management
  - Database schema access

- External Services
  - Weather data
  - Geolocation
  - Calendar operations
  - Math problem solving

- File Processing
  - PDF handling
  - DOCX handling
  - Markdown processing
  - Audio conversion

- Storage
  - DynamoDB for message history
  - S3 for file storage
  - Message retention management

## Setup

1. Environment Variables

The following environment variables need to be set:

```bash
# API Keys
SLACK_BOT_TOKEN=your_slack_token
GOOGLE_API_KEY=your_google_key
GEMINI_API_KEY=your_gemini_key
GOOGLE_CALENDAR_ID=your_calendar_id
ERPNEXT_API_KEY=your_erpnext_key
ERPNEXT_API_SECRET=your_erpnext_secret
OPENAI_API_KEY=your_openai_key
OPENWEATHER_KEY=your_openweather_key
WOLFRAM_ALPHA_APP_ID=your_wolfram_id

# Odoo Configuration
ODOO_URL=your_odoo_url
ODOO_DB=your_odoo_db
ODOO_LOGIN=your_odoo_login
ODOO_PASSWORD=your_odoo_password
```

2. Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

3. AWS Setup

- Create a Lambda function with Python 3.8+ runtime
- Set up the following AWS services:
  - DynamoDB tables
  - S3 buckets
  - IAM roles with appropriate permissions

4. Deployment

Package the code and deploy to AWS Lambda:

```bash
zip -r function.zip .
aws lambda update-function-code --function-name YourFunctionName --zip-file fileb://function.zip
```

## Usage

The assistant responds to various types of messages and commands in Slack:

1. Direct Messages
2. Channel Mentions
3. File Uploads
4. Audio Messages

The assistant can:
- Process natural language requests
- Handle file attachments
- Make API calls to external services
- Interact with Odoo ERP
- Generate and send responses in various formats

## Development

To add new features:

1. Add new service modules in `src/services/`
2. Add new utility functions in `src/utils/`
3. Update configuration in `src/config/`
4. Add new message handlers in `src/handlers/`
5. Update the main Lambda handler as needed

## Testing

Run tests using pytest:

```bash
pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is proprietary and confidential.

## Support

For support, contact the development team.