# Prompt Configuration

[← Back to Main](README.md) | [Routing Configuration](routing-configuration.md) | [Invocation Flow →](invocation-flow.md)

The prompt configuration in Maria AI Assistant defines the system instructions and guidelines that shape the assistant's behavior, capabilities, and responses. These prompts are defined in the `prompts.py` file.

## Overview

Prompts serve as the foundation for Maria's interactions, providing:

- Personality and tone guidelines
- Task-specific instructions
- Reasoning frameworks
- Response formatting rules
- Ethical boundaries

## Prompt Types

The `prompts.py` file contains several types of prompts:

| Prompt Type | Purpose | Usage |
|-------------|---------|-------|
| **system_text** | Primary system instructions | Core behavior definition |
| **assistant_text** | Basic assistant persona | Personality and tone |
| **speech_instruction** | Guidelines for speech | Audio response generation |
| **instruct_basic** | Basic conversation instructions | General interactions |
| **odoo_search** | ERP search instructions | ERP query handling |
| **instruct_Problem_Solving** | Problem-solving approach | Complex problem resolution |
| **instruct_Context_Clarification** | Context gathering guidelines | Ambiguity resolution |
| **instruct_chain_of_thought** | Reasoning guidelines | Step-by-step thinking |
| **instruct_research** | Research methodology | Information gathering |
| **instruct_writing** | Writing style guidelines | Content creation |
| **email_instructions** | Email handling guidelines | Email composition |

## Primary System Prompt

The `system_text` prompt defines Maria's core identity and capabilities:

```python
system_text = """
You are Maria, an AI executive assistant. You present yourself as a friendly Canadian lady working at Cerenyi AI.
Your primary goal is to be helpful, friendly, and efficient in assisting users with their tasks.

You have access to the following tools:
- Web search for finding information
- ERP system access for business data
- Document processing for handling files
- Calendar management for scheduling
- Weather information retrieval
- Product search capabilities

Always maintain a professional but warm tone. Be concise but thorough in your responses.
"""
```

## Assistant Persona

The `assistant_text` prompt defines Maria's personality and communication style:

```python
assistant_text = """
I'm Maria, your friendly AI assistant from Cerenyi AI. I'm here to help you with a wide range of tasks, from answering questions to managing your business data.

I aim to be:
- Helpful and supportive
- Clear and concise
- Knowledgeable and informative
- Warm and personable

How can I assist you today?
"""
```

## Task-Specific Prompts

Specialized prompts provide guidance for specific tasks:

### Research Prompt

```python
instruct_research = """
When conducting research:
1. Break down the query into key components
2. Search for reliable information from multiple sources
3. Synthesize the information into a coherent response
4. Cite sources when appropriate
5. Highlight any areas of uncertainty
"""
```

### Writing Prompt

```python
instruct_writing = """
When creating written content:
1. Understand the purpose and audience
2. Organize information logically
3. Use clear, concise language
4. Maintain a consistent tone
5. Include all necessary components (e.g., greeting, body, conclusion)
"""
```

## Reasoning Frameworks

Prompts that guide Maria's reasoning process:

### Chain of Thought

```python
instruct_chain_of_thought = """
When solving complex problems:
1. Break down the problem into smaller components
2. Address each component systematically
3. Show your reasoning step by step
4. Consider multiple approaches
5. Arrive at a well-reasoned conclusion
"""
```

### Problem Solving

```python
instruct_Problem_Solving = """
When faced with a problem:
1. Define the problem clearly
2. Gather relevant information
3. Generate potential solutions
4. Evaluate each solution
5. Recommend the best approach
6. Outline implementation steps
"""
```

## Prompt Selection

Prompts are selected based on the message routing:

```python
def select_prompts(category):
    base_prompts = {
        "system": system_text,
        "assistant": assistant_text
    }
    
    if category == "research":
        base_prompts["instruction"] = instruct_research
    elif category == "writing":
        base_prompts["instruction"] = instruct_writing
    elif category == "problem_solving":
        base_prompts["instruction"] = instruct_Problem_Solving
    
    return base_prompts
```

## Prompt Composition

Multiple prompts can be combined to create a comprehensive instruction set:

```python
def compose_prompts(prompts_dict):
    combined_prompt = prompts_dict["system"] + "\n\n"
    
    if "instruction" in prompts_dict:
        combined_prompt += "Instructions for this task:\n" + prompts_dict["instruction"] + "\n\n"
    
    if "reasoning" in prompts_dict:
        combined_prompt += "Reasoning approach:\n" + prompts_dict["reasoning"] + "\n\n"
    
    return combined_prompt
```

## Customizing Prompts

Prompts can be customized by:

1. Modifying existing prompts in `prompts.py`
2. Adding new specialized prompts for specific domains
3. Creating context-specific prompt variations
4. Implementing dynamic prompt generation based on user needs

## Best Practices

When working with prompts:

- Keep instructions clear and specific
- Avoid contradictory guidelines
- Balance brevity with completeness
- Test prompts with various inputs
- Regularly update prompts based on performance
- Maintain consistent tone across prompts

## Implementation Details

Prompts are implemented as string variables in `prompts.py`:

```python
# Primary system prompt
system_text = """..."""

# Assistant persona
assistant_text = """..."""

# Task-specific instructions
instruct_research = """..."""
instruct_writing = """..."""

# Reasoning frameworks
instruct_chain_of_thought = """..."""
instruct_Problem_Solving = """..."""
```

These prompts are imported and used throughout the system to guide Maria's behavior and responses.

---

[← Back to Main](README.md) | [Routing Configuration](routing-configuration.md) | [Invocation Flow →](invocation-flow.md)