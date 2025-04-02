# Lambda Function (Main Entry Point)

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [Conversation Management →](conversation-management.md)

The `lambda_handler` in `lambda_function.py` is the main entry point for the Maria AI Assistant system. It serves as the central coordinator that processes incoming Slack events and orchestrates the appropriate response.

## Functionality

The Lambda function:

1. Parses incoming Slack events
2. Retrieves message history
3. Processes any attached files or media
4. Routes the message to the appropriate handler
5. Generates and sends responses

## Key Functions

### lambda_handler

```python
def lambda_handler(event, context):
    # Process Slack event, generate response, and invoke appropriate functions
```

This is the main entry point that AWS Lambda calls when a Slack event is received. It:

- Extracts the event type and relevant data
- Determines the appropriate processing path
- Calls helper functions to generate a response
- Returns the result to the caller

### Web and Search Functions

The lambda function also contains several web interaction functions:

```python
def google_search(search_term, before=None, after=None, intext=None, allintext=None, and_condition=None, must_have=None)
def browse_internet(urls, full_text=False)
async def get_web_pages(urls, full_text=False, max_concurrent_requests=5)
```

These functions allow Maria to search the web and retrieve information from websites.

### Document Management Functions

The lambda function includes document management capabilities:

```python
def send_as_pdf(text, chat_id, title, ts=None)
def list_files(folder_prefix='uploads')
def download_and_read_file(url, content_type)
```

These functions enable Maria to work with documents, including creating PDFs and processing uploaded files.

## Invocation Flow

1. **Event Trigger**: A Slack event (message, mention) triggers the Lambda function
2. **Event Processing**: The function extracts user, channel, and message information
3. **Message Routing**: The message is categorized using the semantic router
4. **Context Building**: Relevant conversation history is retrieved
5. **Response Generation**: A response is generated using the OpenAI API
6. **Tool Execution**: If tools are called, they are executed
7. **Response Delivery**: The final response is sent back to Slack

## Error Handling

The Lambda function includes comprehensive error handling to ensure robustness:

- Catches and logs exceptions
- Provides fallback responses when errors occur
- Retries failed operations when appropriate

## Integration Points

The Lambda function integrates with:

- **Slack API**: For receiving events and sending responses
- **OpenAI API**: For generating responses
- **Storage Layer**: For retrieving and saving messages
- **External Services**: For additional functionality

---

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [Conversation Management →](conversation-management.md)