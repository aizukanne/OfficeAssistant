# Message Management

[← Back to Main](../README.md) | [← Functionality Overview](README.md) | [← Document Processing](document-processing.md) | [User Management →](user-management.md)

Maria handles message routing and maintenance, providing robust capabilities for managing conversations and message history.

## Routing

Message routing determines how different types of messages are processed and handled:

### Routing Configuration

The routing configuration is defined in `routes_layer.json` and maps message patterns to specific handlers:

```json
{
  "chitchat": {
    "patterns": ["hello", "how are you", "tell me about yourself"],
    "system_prompt": "assistant_text",
    "tools": []
  },
  "research": {
    "patterns": ["find information", "search for", "look up"],
    "system_prompt": "instruct_research",
    "tools": ["google_search", "browse_internet"]
  }
}
```

For more details, see the [Routing Configuration](../routing-configuration.md) documentation.

### Routing Process

The routing process follows these steps:

1. Analyze the message content
2. Match against defined patterns
3. Select the appropriate category
4. Apply the corresponding system prompt
5. Make relevant tools available

**Example Usage:**

```
User: Can you find information about climate change?
[System routes this to the "research" category]
Maria: I'll search for information about climate change for you.
[Uses google_search tool to find relevant information]
Here's what I found about climate change:
[Presents search results and summary]
```

## Message History

Maria maintains a comprehensive message history to provide context for conversations:

### Save Messages

```python
def save_message_weaviate(collection_name, chat_id, text, thread=None, image_urls=None)
def save_message(table, chat_id, text, role, thread=None, image_urls=None)
```

These functions save messages to storage systems:

**Parameters:**
- `collection_name`/`table`: The storage collection/table
- `chat_id`: The ID of the chat
- `text`: The message text
- `role`: The role of the sender (for DynamoDB)
- `thread`: (Optional) Thread ID if the message is part of a thread
- `image_urls`: (Optional) List of image URLs associated with the message

**Example:**
```python
save_message_weaviate("messages", "C12345", "Hello, how can I help you today?")
save_message(dynamodb_table, "C12345", "Hello, how can I help you today?", "assistant")
```

### Retrieve Recent Messages

```python
def get_last_messages_weaviate(collection_name, chat_id, num_messages)
def get_last_messages(table, chat_id, num_messages)
```

These functions retrieve the most recent messages:

**Parameters:**
- `collection_name`/`table`: The storage collection/table
- `chat_id`: The ID of the chat
- `num_messages`: The number of messages to retrieve

**Example:**
```python
recent_messages = get_last_messages_weaviate("messages", "C12345", 10)
recent_messages = get_last_messages(dynamodb_table, "C12345", 10)
```

### Find Relevant Messages

```python
def get_relevant_messages(collection_name, chat_id, query_text, num_results)
```

This function performs a semantic search to find messages relevant to a query:

**Parameters:**
- `collection_name`: The name of the Weaviate collection
- `chat_id`: The ID of the chat
- `query_text`: The text to search for
- `num_results`: The number of results to return

**Example:**
```python
relevant_messages = get_relevant_messages("messages", "C12345", "project status", 5)
```

**Example Usage:**

```
User: What did we discuss about the marketing budget last week?
Maria: Let me check our previous conversations about the marketing budget.
Based on our discussion last week, we agreed on a $50,000 budget for Q2, 
with $20,000 allocated to digital advertising and $15,000 to event sponsorships.
You also mentioned wanting to revisit the social media strategy in May.
```

### Get Specific Messages

```python
def get_message_by_sort_id(role, chat_id, sort_id)
def get_messages_in_range(chat_id, start_sort_id, end_sort_id)
```

These functions retrieve specific messages:

**Parameters:**
- `role`: The role of the sender (for `get_message_by_sort_id`)
- `chat_id`: The ID of the chat
- `sort_id`/`start_sort_id`/`end_sort_id`: The sort ID(s) of the message(s)

**Example:**
```python
message = get_message_by_sort_id("user", "C12345", "1234567890")
messages = get_messages_in_range("C12345", "1234567890", "1234567899")
```

## Implementation Details

### Message Storage

Messages are stored in two systems:

1. **DynamoDB**: For structured storage with strong consistency
2. **Weaviate**: For vector-based semantic search

The storage schema includes:

- Chat ID (partition key)
- Timestamp/Sort ID (sort key)
- Message text
- Sender role
- Thread ID (if applicable)
- Media URLs (if applicable)

### Message Retrieval

Message retrieval uses different approaches:

- **Recent messages**: Sorted by timestamp
- **Relevant messages**: Vector similarity search
- **Specific messages**: Direct key lookup

### Message Processing

Before storage, messages undergo processing:

1. Cleaning and normalization
2. Metadata extraction
3. Vector embedding generation (for Weaviate)
4. Media processing (if applicable)

## Message Context Building

Maria builds conversation context using message history:

```python
def build_conversation_context(chat_id, current_message):
    # Get recent message history
    recent_messages = get_last_messages(dynamodb_table, chat_id, 10)
    
    # Find relevant past messages
    relevant_messages = get_relevant_messages("messages", chat_id, current_message, 5)
    
    # Combine and format context
    context = format_conversation_context(recent_messages, relevant_messages)
    
    return context
```

This context is used to:

- Maintain conversation continuity
- Provide relevant background information
- Resolve references to past conversations
- Ensure consistent responses

## Best Practices

When working with message management:

- Use thread IDs consistently for threaded conversations
- Include relevant metadata with messages
- Consider privacy implications when retrieving message history
- Balance context length with relevance
- Implement proper error handling for storage operations

## Future Enhancements

Planned enhancements for message management include:

- Enhanced semantic search capabilities
- Multi-channel message correlation
- Improved context summarization
- Long-term conversation memory
- Personalized context building

---

[← Back to Main](../README.md) | [← Functionality Overview](README.md) | [← Document Processing](document-processing.md) | [User Management →](user-management.md)