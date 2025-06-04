# Maria: AI Executive Assistant Documentation

Maria is an AI executive assistant designed to facilitate communication and task execution within a Slack workspace. Built on Claude 3.7 Sonnet, Maria presents herself as a friendly Canadian lady working at Cerenyi AI. The system integrates with various services including Slack, ERPNext, Amazon, Google APIs, and more to provide a wide range of functionalities.

## Table of Contents

- [System Architecture](system-architecture.md)
- Functionality
  - [Communication](functionality/communication.md)
  - [ERP Integration](functionality/erp-integration.md)
  - [Information Retrieval](functionality/information-retrieval.md)
  - [Document Processing](functionality/document-processing.md)
  - [Message Management](functionality/message-management.md)
  - [User Management](functionality/user-management.md)
  - [Privacy & Security](functionality/privacy-security.md)
- Function Descriptions
  - [Lambda Function](functions/lambda-function.md)
  - [Conversation Management](functions/conversation-management.md)
  - [Storage Operations](functions/storage-operations.md)
  - [Slack Integration](functions/slack-integration.md)
  - [Media Processing](functions/media-processing.md)
  - [Privacy Detection](functions/privacy-detection.md)
  - [ERP Integrations](functions/erp-integrations.md)
  - [External Services](functions/external-services.md)
  - [Web and Search](functions/web-and-search.md)
  - [Document Management](functions/document-management.md)
- [Routing Configuration](routing-configuration.md)
- [Prompt Configuration](prompt-configuration.md)
- [Invocation Flow](invocation-flow.md)
- [Configuration](configuration.md)

## Overview

Maria is a comprehensive AI assistant solution that integrates with various services to provide a wide range of functionalities. The modular design allows for easy maintenance and extension, while the robust conversation handling ensures natural interactions with users.

The system's ability to process and generate text, audio, and images, combined with its integration with ERP systems, web search, and document processing, makes it a versatile tool for enterprise environments.

## Core Modules

- **lambda_function.py**: Main entry point that handles incoming events from Slack
- **conversation.py**: Manages conversation formatting and communication with OpenAI APIs
- **storage.py**: Handles data persistence in DynamoDB and Weaviate
- **slack_integration.py**: Manages interactions with the Slack API
- **media_processing.py**: Handles audio, image, and document processing
- **nlp_utils.py**: Provides natural language processing utilities
- **extservices.py**: Interfaces with external services (calendar, weather, etc.)
- **tools.py**: Defines the available tools and their parameters
- **prompts.py**: Contains system prompts and instructions for different scenarios
- **config.py**: Contains configuration parameters and API connections
- **routes_layer.json**: Defines routing logic based on user utterances
- **erpnext_functions.py**: Provides integration with ERPNext ERP system
- **odoo_functions.py**: Provides integration with Odoo ERP system
- **amazon_functions.py**: Provides integration with Amazon product search

## Getting Started

For detailed information about specific components, please navigate through the documentation using the links in the table of contents above.

To understand the system's architecture and how the components interact, start with the [System Architecture](system-architecture.md) section.

## Documentation Structure

This documentation is organized into multiple Markdown files for better readability and navigation on GitHub. Each file focuses on a specific aspect of the system, with cross-references to related sections where appropriate.