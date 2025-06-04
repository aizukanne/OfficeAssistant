# System Architecture

[← Back to Main](README.md) | [Functionality →](functionality/communication.md)

The application consists of several interconnected modules that work together to provide a comprehensive AI assistant solution.

## Core Modules

1. **lambda_function.py**: Main entry point that handles incoming events from Slack
2. **conversation.py**: Manages conversation formatting and communication with OpenAI APIs
3. **storage.py**: Handles data persistence in DynamoDB and Weaviate
4. **slack_integration.py**: Manages interactions with the Slack API
5. **media_processing.py**: Handles audio, image, and document processing
6. **nlp_utils.py**: Provides natural language processing utilities including PII detection
7. **extservices.py**: Interfaces with external services (calendar, weather, etc.)
8. **tools.py**: Defines the available tools and their parameters
9. **prompts.py**: Contains system prompts and instructions for different scenarios
10. **config.py**: Contains configuration parameters and API connections
11. **routes_layer.json**: Defines routing logic based on user utterances
12. **erpnext_functions.py**: Provides integration with ERPNext ERP system
13. **odoo_functions.py**: Provides integration with Odoo ERP system
14. **amazon_functions.py**: Provides integration with Amazon product search

## Component Interactions

The system follows a modular architecture where each component has a specific responsibility:

- **Lambda Function**: Acts as the entry point for all Slack events and coordinates the flow of information between components
- **Conversation Management**: Handles the formatting and processing of conversations with the AI model
- **Storage Layer**: Provides persistence for messages, user data, and other information
- **Integration Modules**: Connect to external services like Slack, ERPNext, and Odoo
- **Privacy Modules**: Handle PII detection and data protection
- **Utility Modules**: Provide common functionality used across the system

## Data Flow

1. Slack events trigger the Lambda function
2. The Lambda function processes the event and extracts relevant information
3. Message history and context are retrieved from storage
4. PII detection is performed if enabled (optional privacy processing)
5. The message is routed to the appropriate handler based on content
6. External services are called as needed
7. A response is generated and sent back to Slack
8. The interaction is saved to storage for future reference

## Deployment Architecture

The system is deployed as an AWS Lambda function that is triggered by Slack events. It uses:

- **AWS Lambda**: For serverless execution
- **DynamoDB**: For structured data storage
- **Weaviate**: For vector-based message retrieval
- **S3**: For file storage
- **NER Lambda**: For PII detection and privacy processing
- **External APIs**: For additional functionality

---

[← Back to Main](README.md) | [Functionality →](functionality/communication.md)