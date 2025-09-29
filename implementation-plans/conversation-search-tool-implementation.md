# Conversation Search Tool Implementation Plan

## Overview
This document provides step-by-step instructions to implement a conversation search tool that allows LLMs to search through conversation history using semantic similarity. The tool will wrap the existing `get_relevant_messages` function to search both user and assistant message tables.

## Implementation Requirements

The tool should:
- Accept `chat_id` and `query_text` as required parameters
- Have optional `num_results` parameter (default: 5)
- Search both user and assistant message tables simultaneously
- Return structured results from both tables
- Be available to all LLMs (OpenAI, Cerebras, OpenRouter)

## File Changes Required

### 1. Add Tool Definition to `tools.py`

**Location**: Add to the `tools` array before the closing `]` on line 680

```python
    {
        "type": "function",
        "function": {
            "name": "search_conversation_history",
            "description": "Searches the conversation history for relevant messages using semantic similarity. Returns messages from both user and assistant that match the query text, helping to find past discussions, topics, or information that was previously mentioned in the conversation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "The unique chat identifier to search within. This scopes the search to a specific conversation thread."
                    },
                    "query_text": {
                        "type": "string", 
                        "description": "The search query text. This will be matched semantically against past conversation messages to find relevant content."
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return from each table (user and assistant). Defaults to 5 if not specified.",
                        "default": 5
                    }
                },
                "required": ["chat_id", "query_text"]
            }
        }
    }
```

### 2. Implement Function in `lambda_function.py`

#### A. Add Function Implementation

Add this function anywhere in the file (suggested: after line 620):

```python
def search_conversation_history(chat_id, query_text, num_results=5):
    """
    Wrapper function to search both user and assistant message tables.
    Returns results from both tables in a structured dictionary.
    
    Args:
        chat_id (str): The unique chat identifier to search within
        query_text (str): The search query text for semantic matching
        num_results (int): Maximum number of results from each table (default: 5)
        
    Returns:
        dict: Dictionary containing user_messages, assistant_messages, total_results, query, and chat_id
    """
    from config import user_table, assistant_table
    from storage_pooled import get_relevant_messages_pooled
    
    try:
        # Search user messages
        user_results = get_relevant_messages_pooled(user_table, chat_id, query_text, num_results)
        
        # Search assistant messages  
        assistant_results = get_relevant_messages_pooled(assistant_table, chat_id, query_text, num_results)
        
        return {
            "user_messages": user_results,
            "assistant_messages": assistant_results,
            "total_results": len(user_results) + len(assistant_results),
            "query": query_text,
            "chat_id": chat_id
        }
        
    except Exception as e:
        return {
            "error": f"Failed to search conversation history: {str(e)}",
            "user_messages": [],
            "assistant_messages": [],
            "total_results": 0,
            "query": query_text,
            "chat_id": chat_id
        }
```

#### B. Add to Available Functions Mapping

**Location**: In the `get_available_functions()` function, add to the `common_functions` dictionary at line ~522:

```python
        "search_conversation_history": search_conversation_history,
```

The complete `common_functions` dictionary should look like this:

```python
    # Common functions available to all platforms
    common_functions = {
        "browse_internet": browse_internet,
        "google_search": google_search,
        "get_coordinates": get_coordinates,
        "get_weather_data": get_weather_data,
        "get_message_by_sort_id": get_message_by_sort_id,
        "get_messages_in_range": get_messages_in_range,
        "get_users": get_users,
        "get_channels": get_channels,
        "send_as_pdf": send_as_pdf,
        "list_files": list_files,
        "solve_maths": solve_maths,
        "odoo_get_mapped_models": odoo_get_mapped_models,
        #"odoo_get_mapped_fields": odoo_get_mapped_fields,
        "odoo_create_record": odoo_create_record,
        "odoo_fetch_records": odoo_fetch_records,
        "odoo_update_record": odoo_update_record,
        "odoo_delete_record": odoo_delete_record,
        "odoo_print_record": odoo_print_record,
        "odoo_post_record": odoo_post_record,
        "ask_openai_o1": ask_openai_o1,
        "get_embedding": get_embedding,
        "manage_mute_status": manage_mute_status,
        "search_and_format_products": search_and_format_products,
        "gemini_generate_content": gemini_generate_content,
        "search_conversation_history": search_conversation_history,
    }
```

### 3. Enable for Cerebras in `conversation.py`

**Location**: In the `select_cerebras_tools()` function, add to the `tool_names` set at line ~574:

```python
        "search_conversation_history",
```

The complete `tool_names` set should look like this:

```python
    tool_names = {
        "browse_internet",
        "google_search",
        "get_coordinates",
        "get_weather_data",
        "get_message_by_sort_id",
        "get_messages_in_range",
        "get_users",
        "get_channels",
        "manage_mute_status",
        "search_and_format_products",
        "set_slack_channel_description",
        "create_slack_channel",
        "invite_users_to_slack_channel",
        "gemini_generate_content",
        "search_conversation_history"
    }
```

## Implementation Checklist

- [ ] **Step 1**: Add tool definition to `tools.py`
- [ ] **Step 2**: Implement `search_conversation_history()` function in `lambda_function.py`
- [ ] **Step 3**: Add function to `common_functions` mapping in `get_available_functions()`
- [ ] **Step 4**: Add function name to `tool_names` set in `select_cerebras_tools()`
- [ ] **Step 5**: Test implementation (see testing section below)

## Testing

After implementation, verify the tool works by:

1. **Check function import**: Ensure the function is properly imported and available
2. **Test function mapping**: Verify it appears in `get_available_functions()` output for all platforms
3. **Test Cerebras filtering**: Confirm it's included in Cerebras tool selection
4. **Test function execution**: Call the function directly with test parameters

### Test Script Reference

You can use patterns from `test_complete_integration.py` to create automated tests:

```python
def test_conversation_search_tool():
    """Test conversation search tool implementation"""
    from lambda_function import get_available_functions, search_conversation_history
    
    # Test function availability
    platforms = ['slack', 'telegram', 'unknown']
    for platform in platforms:
        available = get_available_functions(platform)
        assert 'search_conversation_history' in available, f"Function missing for {platform}"
    
    # Test function execution
    result = search_conversation_history("test_chat", "test query", 3)
    assert 'user_messages' in result
    assert 'assistant_messages' in result
    assert 'total_results' in result
    
    print("✅ Conversation search tool implementation verified")
```

## Technical Details

### Function Behavior
- **Input**: `chat_id`, `query_text`, optional `num_results`
- **Process**: Calls `get_relevant_messages_pooled()` for both user and assistant tables
- **Output**: Dictionary with separate user/assistant results plus metadata
- **Error Handling**: Returns structured error response on failure

### Dependencies
- Uses existing `get_relevant_messages_pooled()` from `storage_pooled.py`
- Imports `user_table` and `assistant_table` from `config.py`
- Leverages Weaviate connection pooling for performance

### Integration Points
- **Tools Definition**: `tools.py` - Defines LLM interface
- **Function Mapping**: `lambda_function.py` - Makes available to all LLMs
- **Cerebras Filter**: `conversation.py` - Enables for Cerebras specifically

## Expected Outcome

Once implemented, LLMs will be able to search conversation history using natural language queries like:
- "What did we discuss about the project timeline?"
- "Find messages about database errors"
- "Search for conversations about API integration"

The tool returns both user and assistant messages that semantically match the query, providing comprehensive context from conversation history.