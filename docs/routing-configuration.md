# Routing Configuration

[← Back to Main](README.md) | [System Architecture](system-architecture.md) | [Prompt Configuration →](prompt-configuration.md)

The routing configuration in Maria AI Assistant determines how different types of user inquiries are processed and handled. This is defined in the `routes_layer.json` file, which maps user intents to specific handling strategies.

## Overview

The routing system:

- Categorizes incoming messages based on content and context
- Directs messages to the appropriate handling logic
- Selects the most relevant system prompts
- Determines which tools and capabilities to activate

## Routing Categories

The `routes_layer.json` file defines several routing categories:

| Category | Description | Example Queries |
|----------|-------------|----------------|
| **chitchat** | Casual conversation handling | "How are you today?", "Tell me a joke" |
| **research** | Information retrieval inquiries | "What's the capital of France?", "Research quantum computing" |
| **writing** | Content generation requests | "Write an email to my team", "Draft a project proposal" |
| **numerical_analysis** | Computational and data analysis | "Calculate the ROI for this project", "Analyze these sales figures" |
| **navigation** | Location and direction-related | "How do I get to the office?", "Find nearby restaurants" |
| **odoo_erp** | ERP-related queries and operations | "Show me recent sales orders", "Create a new customer" |

## Routing Structure

The routing configuration follows this structure:

```json
{
  "category_name": {
    "patterns": [
      "pattern1",
      "pattern2"
    ],
    "system_prompt": "prompt_name",
    "tools": [
      "tool1",
      "tool2"
    ]
  }
}
```

Where:
- `category_name`: The name of the routing category
- `patterns`: List of patterns or keywords that trigger this category
- `system_prompt`: The name of the system prompt to use
- `tools`: List of tools to make available for this category

## Routing Process

When a message is received:

1. The message text is analyzed against the patterns in each category
2. The best matching category is selected
3. The corresponding system prompt is loaded
4. The specified tools are made available
5. The message is processed with the selected configuration

## Example Configuration

Here's an example of how the routing configuration might look:

```json
{
  "chitchat": {
    "patterns": [
      "hello",
      "how are you",
      "tell me about yourself",
      "joke"
    ],
    "system_prompt": "assistant_text",
    "tools": []
  },
  "research": {
    "patterns": [
      "find information",
      "search for",
      "look up",
      "research",
      "what is"
    ],
    "system_prompt": "instruct_research",
    "tools": [
      "google_search",
      "browse_internet"
    ]
  },
  "writing": {
    "patterns": [
      "write",
      "draft",
      "compose",
      "create a document",
      "email"
    ],
    "system_prompt": "instruct_writing",
    "tools": [
      "send_as_pdf"
    ]
  }
}
```

## Customizing Routing

The routing configuration can be customized by:

1. Adding new categories for specific domains
2. Expanding pattern lists to improve matching
3. Creating specialized system prompts for different scenarios
4. Configuring tool availability based on the task

## Implementation Details

The routing system is implemented in the main Lambda function:

```python
def route_message(message_text, user_context):
    # Analyze message against routing patterns
    category = determine_category(message_text, routes_config)
    
    # Load appropriate system prompt
    system_prompt = prompts[routes_config[category]["system_prompt"]]
    
    # Configure available tools
    available_tools = routes_config[category]["tools"]
    
    return {
        "category": category,
        "system_prompt": system_prompt,
        "available_tools": available_tools
    }
```

## Best Practices

When working with the routing configuration:

- Use specific, distinctive patterns for each category
- Prioritize more specific categories over general ones
- Regularly update patterns based on user interactions
- Test routing with a variety of user inputs
- Monitor routing accuracy and adjust as needed

## Advanced Routing Features

The routing system also supports:

- Context-aware routing based on conversation history
- Multi-category matching for complex queries
- Fallback handling for unmatched queries
- Dynamic tool selection based on query content

---

[← Back to Main](README.md) | [System Architecture](system-architecture.md) | [Prompt Configuration →](prompt-configuration.md)