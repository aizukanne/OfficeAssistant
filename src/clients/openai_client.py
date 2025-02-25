import os
import json
import openai
import requests
import base64
import tempfile
from decimal import Decimal
from bson import ObjectId

from ..core.config import OPENAI_TOOLS

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def make_openai_call(client, conversations, temperature=None, model="gpt-4o-2024-11-20"):
    """
    Makes a call to the OpenAI API with the specified parameters.
    This function consolidates the previous make_openai_api_call and make_openai_vision_call functions.

    Args:
        client: The OpenAI client instance
        conversations: The conversation messages to send
        temperature: Optional temperature parameter for controlling response randomness
        model: The model to use (defaults to gpt-4o-2024-11-20)

    Returns:
        The message from the API response, or None if an error occurs
    """
    try:
        # Prepare the API call parameters
        params = {
            "model": model,
            "messages": conversations,
            "max_tokens": 5500,
            "tools": OPENAI_TOOLS  # This will need to be imported from config
        }
        
        # Add temperature parameter only if it's provided
        if temperature is not None:
            params["temperature"] = temperature

        # Make the API call
        response = client.chat.completions.create(**params)
        print(response)
        return response.choices[0].message
    except Exception as e:
        print(f"An error occurred during the OpenAI API call: {e}")
        return None

def make_openai_audio_call(client, conversations):
    """
    Sends the constructed conversation to OpenAI's chat completion API for audio processing.

    Args:
        client: OpenAI client instance.
        conversations (list): The list of messages for the conversation.

    Returns:
        dict: OpenAI message object with audio file path and transcript in `message.audio`.
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
    }
    payload = {
        "model": "gpt-4o-audio-preview-2024-12-17",
        "modalities": ["text", "audio"],
        "audio": {"voice": "shimmer", "format": "mp3"},
        "messages": conversations,
        "max_tokens": 5500,
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        result = response.json()
        print(f"Openai Response: {result}")
        
        message = result["choices"][0]["message"]

        # Check if audio is present
        if "audio" in message:
            # Decode audio and write to a temporary file
            audio_data = base64.b64decode(message["audio"]["data"])
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio_file:
                tmp_audio_file.write(audio_data)
                audio_file_path = tmp_audio_file.name

            # Update the audio object with the file path
            message["audio"]["file_path"] = audio_file_path
            del message["audio"]["data"]

        print(f"Openai Modified Response: {message}")

        return message

    except requests.exceptions.RequestException as e:
        # Handle HTTP errors
        if hasattr(e, 'response'):
            print(f"Status code: {e.response.status_code}")
            print(f"Error response: {e.response.json()}")  # OpenAI sends error details in JSON
            print(f"Headers: {e.response.headers}")
        else:
            print(f"Error with no response: {str(e)}")
        return None
    except KeyError as e:
        # Handle missing keys in the JSON response
        print(f"KeyError: Missing expected key in response: {e}")
        return None
    except Exception as e:
        # Handle unexpected errors
        print(f"Unexpected error: {str(e)}")
        return None

def ask_openai_o1(prompt):
    print(f'OpenAI o1 Prompt: {prompt}')
    message = [
        {
            "role": "user",
            "content": prompt
        }       
    ]

    try:
        # Prepare the API call   
        response = client.chat.completions.create(
            model="o1",
            messages=message
        )
        print(f'OpenAI o1: {response}')
        
        # Extract the actual message content using dot notation
        response_message_content = response.choices[0].message.content

        # Return the serialized content
        return json.dumps(response_message_content, default=decimal_default)
    except Exception as e:
        print(f"An error occurred during the OpenAI o1 API call: {e}")
        return None

def get_embedding(text, model="text-embedding-ada-002"):
    text_cleaned = text.replace("\n", " ")
    embedding = client.embeddings.create(input=[text_cleaned], model=model).data[0].embedding
    return {"text": text_cleaned, "embedding": embedding}

def text_to_speech(text, file_suffix=".mp3"):
    """
    Converts text to speech and saves the audio to a temporary file.

    Parameters:
    - text: The text to be converted to speech.
    - file_suffix: The suffix for the temporary file.

    Returns:  
    - The path to the saved speech file.    
    """
    with tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False) as tmp_file:
        response = client.audio.speech.create(
            model="tts-1",
            voice="shimmer",
            input=text
        )
        response.stream_to_file(tmp_file.name)
        tmp_file_path = tmp_file.name

    return tmp_file_path

# Helper function for JSON serialization
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, ObjectId):
        return str(obj)  # Convert ObjectId to string
    raise TypeError("Unserializable object {} of type {}".format(obj, type(obj)))