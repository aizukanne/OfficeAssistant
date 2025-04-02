# Storage Operations

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [← Lambda Function](lambda-function.md) | [Conversation Management →](conversation-management.md)

The storage operations module in `storage.py` provides functionality for persisting and retrieving data from various storage systems, including DynamoDB and Weaviate.

## Overview

The storage module handles:

- Message storage and retrieval
- Vector-based semantic search
- User and channel information management
- Mute status management

## Weaviate Operations

Weaviate is used for vector-based storage and retrieval, enabling semantic search capabilities.

### Key Functions

```python
def save_message_weaviate(collection_name, chat_id, text, thread=None, image_urls=None)
def get_last_messages_weaviate(collection_name, chat_id, num_messages)
def get_relevant_messages(collection_name, chat_id, query_text, num_results)
```

### save_message_weaviate

Saves a message to the Weaviate vector database.

**Parameters:**
- `collection_name`: The name of the Weaviate collection
- `chat_id`: The ID of the chat
- `text`: The message text
- `thread`: (Optional) Thread ID if the message is part of a thread
- `image_urls`: (Optional) List of image URLs associated with the message

**Example:**
```python
save_message_weaviate("messages", "C12345", "Hello, how can I help you today?")
```

### get_last_messages_weaviate

Retrieves the most recent messages from Weaviate.

**Parameters:**
- `collection_name`: The name of the Weaviate collection
- `chat_id`: The ID of the chat
- `num_messages`: The number of messages to retrieve

**Example:**
```python
messages = get_last_messages_weaviate("messages", "C12345", 10)
```

### get_relevant_messages

Performs a semantic search to find messages relevant to a query.

**Parameters:**
- `collection_name`: The name of the Weaviate collection
- `chat_id`: The ID of the chat
- `query_text`: The text to search for
- `num_results`: The number of results to return

**Example:**
```python
relevant_messages = get_relevant_messages("messages", "C12345", "project status", 5)
```

## DynamoDB Operations

DynamoDB is used for structured data storage with strong consistency guarantees.

### Key Functions

```python
def save_message(table, chat_id, text, role, thread=None, image_urls=None)
def get_last_messages(table, chat_id, num_messages)
def get_message_by_sort_id(role, chat_id, sort_id)
def get_messages_in_range(chat_id, start_sort_id, end_sort_id)
```

### save_message

Saves a message to DynamoDB.

**Parameters:**
- `table`: The DynamoDB table
- `chat_id`: The ID of the chat
- `text`: The message text
- `role`: The role of the sender (user, assistant, etc.)
- `thread`: (Optional) Thread ID if the message is part of a thread
- `image_urls`: (Optional) List of image URLs associated with the message

**Example:**
```python
save_message(dynamodb_table, "C12345", "Hello, how can I help you today?", "assistant")
```

### get_last_messages

Retrieves the most recent messages from DynamoDB.

**Parameters:**
- `table`: The DynamoDB table
- `chat_id`: The ID of the chat
- `num_messages`: The number of messages to retrieve

**Example:**
```python
messages = get_last_messages(dynamodb_table, "C12345", 10)
```

### get_message_by_sort_id

Retrieves a specific message by its sort ID.

**Parameters:**
- `role`: The role of the sender
- `chat_id`: The ID of the chat
- `sort_id`: The sort ID of the message

**Example:**
```python
message = get_message_by_sort_id("user", "C12345", "1234567890")
```

### get_messages_in_range

Retrieves messages within a specific sort ID range.

**Parameters:**
- `chat_id`: The ID of the chat
- `start_sort_id`: The starting sort ID
- `end_sort_id`: The ending sort ID

**Example:**
```python
messages = get_messages_in_range("C12345", "1234567890", "1234567899")
```

## User and Channel Management

Functions for managing user and channel information.

### Key Functions

```python
def get_users(user_id=None)
def get_channels(id=None)
def manage_mute_status(chat_id, status=None)
```

### get_users

Retrieves user information.

**Parameters:**
- `user_id`: (Optional) The ID of a specific user to retrieve

**Example:**
```python
# Get all users
all_users = get_users()

# Get a specific user
user = get_users("U12345")
```

### get_channels

Retrieves channel information.

**Parameters:**
- `id`: (Optional) The ID of a specific channel to retrieve

**Example:**
```python
# Get all channels
all_channels = get_channels()

# Get a specific channel
channel = get_channels("C12345")
```

### manage_mute_status

Manages the mute status of a chat.

**Parameters:**
- `chat_id`: The ID of the chat
- `status`: (Optional) The new mute status (True/False)

**Example:**
```python
# Mute a chat
manage_mute_status("C12345", True)

# Unmute a chat
manage_mute_status("C12345", False)

# Get current mute status
status = manage_mute_status("C12345")
```

## Implementation Details

The storage module uses:

- AWS DynamoDB for structured data storage
- Weaviate for vector-based semantic search
- Boto3 for AWS SDK interactions
- Connection pooling for performance optimization
- Error handling and retry logic for resilience

## Best Practices

When working with the storage module:

- Use Weaviate for semantic search and DynamoDB for structured data
- Implement proper error handling for storage operations
- Consider pagination for large result sets
- Use batch operations when possible for performance
- Implement caching for frequently accessed data

---

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [← Lambda Function](lambda-function.md) | [Conversation Management →](conversation-management.md)