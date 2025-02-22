import json
import logging
import os
import requests
from typing import Dict, List, Optional, Any, Union

import openai
from openai import OpenAIError, BadRequestError

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def make_openai_api_call(
    client: openai.OpenAI,
    conversations: List[Dict],
    temperature: float = 0.9,
    model: str = "gpt-4o-2024-11-20",
    max_tokens: int = 5500,
    tools: Optional[List[Dict]] = None
) -> Optional[Any]:
    """
    Makes a standard API call to OpenAI's chat completion endpoint.
    
    Args:
        client: The OpenAI client instance
        conversations: The conversation history
        temperature: The sampling temperature (default: 0.9)
        model: The model to use (default: gpt-4o-2024-11-20)
        max_tokens: Maximum tokens to generate (default: 5500)
        tools: Optional list of tools to include
        
    Returns:
        Optional[Any]: The response message or None if an error occurs
    """
    try:
        # Prepare the API call 
        response = client.chat.completions.create(
            temperature=temperature,
            model=model,
            messages=conversations,
            max_tokens=max_tokens,
            tools=tools
        )
        print(response)
        return response.choices[0].message
    except Exception as e:
        print(f"An error occurred during the OpenAI API call: {e}")
        return None

def make_openai_vision_call(
    client: openai.OpenAI,
    conversations: List[Dict],
    temperature: float = 0.9,
    model: str = "gpt-4o-2024-11-20",
    max_tokens: int = 5500,
    tools: Optional[List[Dict]] = None
) -> Optional[Any]:
    """
    Makes a vision-enabled API call to OpenAI's chat completion endpoint.
    
    Args:
        client: The OpenAI client instance
        conversations: The conversation history with vision content
        temperature: The sampling temperature (default: 0.9)
        model: The model to use (default: gpt-4o-2024-11-20)
        max_tokens: Maximum tokens to generate (default: 5500)
        tools: Optional list of tools to include
        
    Returns:
        Optional[Any]: The response message or None if an error occurs
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=conversations,
            max_tokens=max_tokens,
            tools=tools
        )
        print(response)
        return response.choices[0].message
    except Exception as e:
        print(f"An error occurred during the OpenAI Vision API call: {e}")
        return None

def make_openai_audio_call(
    client: openai.OpenAI,
    conversations: List[Dict],
    openai_api_key: str,
    model: str = "gpt-4o-audio-preview-2024-12-17",
    max_tokens: int = 5500
) -> Optional[Dict]:
    """
    Makes an audio-enabled API call to OpenAI's chat completion endpoint.
    
    Args:
        client: The OpenAI client instance
        conversations: The conversation history with audio content
        openai_api_key: The OpenAI API key
        model: The model to use (default: gpt-4o-audio-preview-2024-12-17)
        max_tokens: Maximum tokens to generate (default: 5500)
        
    Returns:
        Optional[Dict]: The response message or None if an error occurs
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}",
    }
    payload = {
        "model": model,
        "modalities": ["text", "audio"],
        "audio": {"voice": "shimmer", "format": "mp3"},
        "messages": conversations,
        "max_tokens": max_tokens,
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        print(f"OpenAI Response: {result}")
        message = result["choices"][0]["message"]
        
        if "audio" in message:
            audio_data = base64.b64decode(message["audio"]["data"])
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio_file:
                tmp_audio_file.write(audio_data)
                audio_file_path = tmp_audio_file.name
            message["audio"]["file_path"] = audio_file_path
            del message["audio"]["data"]
            
        print(f"OpenAI Modified Response: {message}")
        return message
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response'):
            print(f"Status code: {e.response.status_code}")
            print(f"Error response: {e.response.json()}")
            print(f"Headers: {e.response.headers}")
        else:
            print(f"Error with no response: {str(e)}")
        return None
    except KeyError as e:
        print(f"KeyError: Missing expected key in response: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None

def ask_openai_o1(prompt: str) -> Optional[str]:
    """
    Makes an API call to OpenAI's o1 model for advanced reasoning tasks.
    
    Args:
        prompt: The text prompt to send to the model
        
    Returns:
        Optional[str]: The model's response or None if an error occurs
    """
    print(f'OpenAI o1 Prompt: {prompt}')
    message = [
        {
            "role": "user",
            "content": prompt
        }       
    ]
    try: 
        response = client.chat.completions.create(
            model="o1",
            messages=message
        )
        print(f'OpenAI o1: {response}')
        response_message_content = response.choices[0].message.content
        return json.dumps(response_message_content, default=decimal_default)
    except Exception as e:
        print(f"An error occurred during the OpenAI o1 API call: {e}")
        return None

def get_embedding(text: str, model: str = "text-embedding-ada-002") -> Optional[List[float]]:
    """
    Generates an embedding for the given text using OpenAI's embedding model.
    
    Args:
        text: The text to generate an embedding for
        model: The embedding model to use (default: text-embedding-ada-002)
        
    Returns:
        Optional[List[float]]: The embedding vector or None if an error occurs
    """
    try:
        response = client.embeddings.create(
            model=model,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def serialize_chat_completion_message(message: Any) -> Dict:
    """
    Serializes a ChatCompletionMessage object into a dictionary format.
    
    Args:
        message: The ChatCompletionMessage to serialize
        
    Returns:
        Dict: The serialized message
    """
    return {
        "role": message.role,
        "content": message.content,
        "tool_calls": [
            {
                "id": tool_call.id,
                "type": tool_call.type,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments
                }
            }
            for tool_call in message.tool_calls
        ] if message.tool_calls else None
    }