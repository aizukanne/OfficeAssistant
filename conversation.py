import json
import time
import datetime
from cerebras_tool_converter import convert_tools_for_cerebras
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import requests
from typing import List, Dict, Any, Optional

from config import client, cerebras_api_key, ai_temperature, slack_bot_token
from tools import tools  # Import tools from tools.py
from storage import decimal_default

from slack_integration import send_slack_message, send_audio_to_slack
from storage import save_message_weaviate

# Import the messaging router for unified message sending
try:
    from messaging.router import get_global_router
    MESSAGE_ROUTER_AVAILABLE = True
except ImportError:
    MESSAGE_ROUTER_AVAILABLE = False
    print("Warning: MessageRouter not available, falling back to Slack-only messaging")


def make_text_conversation(system_text, assistant_text, display_name, msg_history_summary, all_messages, text):
    current_datetime = datetime.datetime.now(datetime.timezone.utc)
    datetime_msg = f"Today is {current_datetime.strftime('%A %d %B %Y')} and the time is {current_datetime.strftime('%I:%M %p')} GMT. Use this to accurately understand statements involving relative time, such as 'tomorrow', 'last week', last year or any other reference of time."    
    # Initialize conversation array         
    conversation = [
        { "role": "system", "content": system_text },
        { "role": "assistant", "content": assistant_text}        
    ]

    conversation.append({ 
        "role": "assistant", 
        "content": (json.dumps(msg_history_summary, default=decimal_default))
    })
    
    # Add them to the conversation array   
    for message in all_messages:
        conversation.append({
            "role": message['role'],
            "content": message['message']
        }) 

    conversation.append({
        "role": "assistant",
        "content": "All the previous messages are a trail of the message history to aid your understanding of the conversation. The next message is the current request from the user."
    })   

    conversation.append({
        "role": "assistant",
        "content": datetime_msg
    })       
    
    if display_name is not None and display_name != "":
        conversation.append({
            "role": "user",
            "content": text,
            "name": display_name
        })
    else:
        conversation.append({
            "role": "user",
            "content": text
        })

    print(json.dumps(conversation))         
    
    return conversation 


def make_vision_conversation(system_text, assistant_text, display_name, all_relevant_messages, msg_history_summary, all_messages, text, image_urls=None): 
    current_datetime = datetime.datetime.now(datetime.timezone.utc)
    datetime_msg = f"Today is {current_datetime.strftime('%A %d %B %Y')} and the time is {current_datetime.strftime('%I:%M %p')} GMT. Use this to accurately understand statements involving relative time, such as 'tomorrow', 'last week', last year or any other reference of time."
    
    # Initialize conversation array  
    conversation = [
        { "role": "system", "content": [{"type": "text", "text": system_text}] },
        { "role": "assistant", "content": [{"type": "text", "text": assistant_text}]}
    ]

    conversation.append({
        "role": "assistant",
        "content": [{"type": "text", "text": "Here is some relevant information from past conversations which may contain information that could provide additional context or information."}]
    })      

    conversation.append({ 
        "role": "assistant", 
        "content": [{"type": "text", "text": json.dumps(all_relevant_messages, default=decimal_default)}]
    })

    conversation.append({ 
        "role": "assistant", 
        "content": [{"type": "text", "text": json.dumps(msg_history_summary, default=decimal_default)}]
    })

    # Add them to the conversation array  
    for message in all_messages:
        # Start with the text content
        content = [{"type": "text", "text": message['message']}]
        
        # Check if there are image_urls in the message and add them to the content
        if "image_urls" in message:
            for url in message["image_urls"]:
                if url:  # Ensure the URL is not empty
                    content.append({"type": "image_url", "image_url": {"url": url}})
        
        # Add the constructed content to the conversation
        conversation.append({
            "role": message['role'],
            "content": content  
        })

    conversation.append({
        "role": "assistant",
        "content": "All the previous messages are a trail of the message history to aid your understanding of the conversation. The next message is the current request from the user."
    })

    conversation.append({
        "role": "assistant",
        "content": datetime_msg
    })        

    # Add final user message, optionally with image  
    user_content = [{"type": "text", "text": text}]

    # Assuming user_content is already defined and is a list  
    if image_urls is not None:
        for url in image_urls:
            if url:  # Check if the URL is not empty
                user_content.append({"type": "image_url", "image_url": {"url": url}})

    if display_name is not None and display_name != "":
        conversation.append({
            "role": "user",
            "content": user_content,
            "name": display_name
        })
    else:
        conversation.append({
            "role": "user",
            "content": user_content
        })

    print(json.dumps(conversation))    
    
    return conversation


def make_audio_conversation(system_text, assistant_text, display_name, all_relevant_messages, msg_history_summary, all_messages, text, audio_urls=None):
    """
    Constructs the conversation payload for audio inputs by encoding audio files in base64.
    Accepts the same parameters as make_vision_conversation for consistency.
    """
    current_datetime = datetime.datetime.now(datetime.timezone.utc)
    datetime_msg = f"Today is {current_datetime.strftime('%A %d %B %Y')} and the time is {current_datetime.strftime('%I:%M %p')} GMT. Use this to accurately understand statements involving relative time, such as 'tomorrow', 'last week', last year or any other reference of time."
    
    # Initialize conversation array
    conversation = [
        {"role": "system", "content": [{"type": "text", "text": system_text}]},
        {"role": "assistant", "content": [{"type": "text", "text": assistant_text}]},
    ]

    conversation.append({
        "role": "assistant",
        "content": [{"type": "text", "text": "Here is some relevant information from past conversations which may contain information that could provide additional context or information."}]
    })

    conversation.append({ 
        "role": "assistant", 
        "content": [{"type": "text", "text": json.dumps(all_relevant_messages, default=decimal_default)}]
    })

    conversation.append({ 
        "role": "assistant", 
        "content": [{"type": "text", "text": json.dumps(msg_history_summary, default=decimal_default)}]
    })

    # Add historical messages
    for message in all_messages:
        # Start with the text content
        content = [{"type": "text", "text": message['message']}]
              
        # Add the constructed content to the conversation
        conversation.append({
            "role": message['role'],
            "content": content  
        })

    conversation.append({
        "role": "assistant",
        "content": [{"type": "text", "text": "All the previous messages are a trail of the message history to aid your understanding of the conversation. The next message is the current request from the user."}]
    })

    conversation.append({
        "role": "assistant",
        "content": [{"type": "text", "text": datetime_msg}]
    })

    # Add the user's current message
    user_content = [{"type": "text", "text": text}]
    
    # Process audio files if present
    if audio_urls is not None:
        import requests
        import base64
        from media_processing import convert_to_wav_in_memory

        for url in audio_urls:
            if url:
                # Get the Slack headers since these are Slack URLs
                headers = {
                    'Authorization': f'Bearer {slack_bot_token}'
                }
                
                try:
                    # Download the audio
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                    audio_data = response.content

                    # Convert to WAV format if needed
                    wav_data = convert_to_wav_in_memory(audio_data)

                    # Base64 encode
                    encoded_string = base64.b64encode(wav_data).decode("utf-8")
                    
                    # Add to user content
                    user_content.append({
                        "type": "input_audio",
                        "input_audio": {
                            "data": encoded_string,
                            "format": "wav"
                        }
                    })
                except Exception as e:
                    print(f"Error processing audio URL {url}: {str(e)}")
                    # Continue with other URLs if one fails

    if display_name is not None and display_name != "":
        conversation.append({
            "role": "user",
            "content": user_content,
            "name": display_name
        })
    else:
        conversation.append({
            "role": "user",
            "content": user_content
        })
    
    print(f"Audio Conversation created with {len(conversation)} messages")
    
    return conversation


def make_cerebras_conversation(system_text, assistant_text, display_name, all_relevant_messages, msg_history_summary, all_messages, text, image_urls=None):
    """
    Create a conversation format specifically for Cerebras API.
    Uses simple string content format that Cerebras expects.
    
    Args:
        system_text (str): System prompt text
        assistant_text (str): Initial assistant message
        display_name (str): User's display name  
        all_relevant_messages (list): Relevant message history
        msg_history_summary (list): Summary of message history
        all_messages (list): All messages in conversation
        text (str): Current user message text
        image_urls (list): Image URLs (ignored - Cerebras doesn't support images)
        
    Returns:
        list: Conversation array formatted for Cerebras API
    """
    
    current_datetime = datetime.datetime.now(datetime.timezone.utc)
    datetime_msg = f"Today is {current_datetime.strftime('%A %d %B %Y')} and the time is {current_datetime.strftime('%I:%M %p')} GMT. Use this to accurately understand statements involving relative time, such as 'tomorrow', 'last week', last year or any other reference of time."

    # Build conversation with simple string content (Cerebras format)
    conversation = [
        {"role": "system", "content": system_text},
        {"role": "assistant", "content": assistant_text}
    ]

    conversation.append({
        "role": "assistant",
        "content": "Here is some relevant information from past conversations which may contain information that could provide additional context or information."
    })      

    conversation.append({ 
        "role": "assistant", 
        "content": json.dumps(all_relevant_messages, default=decimal_default)
    })

    conversation.append({ 
        "role": "assistant", 
        "content": json.dumps(msg_history_summary, default=decimal_default)
    })

    # Add historical messages - simple string content only
    for message in all_messages:
        conversation.append({
            "role": message['role'],
            "content": str(message['message'])  # Simple string content
        })

    conversation.append({
        "role": "assistant",
        "content": "All the previous messages are a trail of the message history to aid your understanding of the conversation. The next message is the current request from the user."
    })

    conversation.append({
        "role": "assistant",
        "content": datetime_msg
    })        

    # Add final user message - simple format
    final_message = {
        "role": "user",
        "content": text  # Simple string content
    }
    
    if display_name is not None and display_name != "":
        final_message["name"] = display_name
    
    conversation.append(final_message)

    print(json.dumps(conversation)) 
    
    return conversation


def make_openai_vision_call(client, conversations):
    try:
        # Prepare the API call   
        response = client.chat.completions.create(
            temperature=ai_temperature,
            model="gpt-4o-2024-11-20",
            messages=conversations,
            max_tokens=5500,
            tools=tools
        )
        print(response)
        return response.choices[0].message
    except Exception as e:
        print(f"An error occurred during the OpenAI Vision API call: {e}")
        return None


def make_openai_audio_call(client, conversations):
    try:
        # Prepare the API call 
        response = client.chat.completions.create(
            model="gpt-4o-audio-preview",
            messages=conversations,
            temperature=ai_temperature,
            max_tokens=5500,
            tools=tools,
            modalities=["text", "audio"],
            audio={
                "voice": "alloy",
                "format": "mp3"  # Using mp3 for better compatibility
            }
        )
        print(response)
        return response.choices[0].message
    except Exception as e:
        print(f"An error occurred during the OpenAI API call: {e}")
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


def make_cerebras_call(conversations, model="llama-4-scout-17b-16e-instruct", max_tokens=2500):
    """
    Make a Cerebras API call similar to OpenAI format
    
    Args:
        conversations (list): Array of message dictionaries
        model (str): Model name to use
        max_tokens (int): Maximum tokens to generate
        
    Returns:
        dict: Message object from response, or None if error
    """
    cerebras_tools = select_cerebras_tools(tools)
    cerebras_compatible_tools = ensure_object_properties(convert_tools_for_cerebras(cerebras_tools))

    try:
        url = "https://api.cerebras.ai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {cerebras_api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare the payload - keep it minimal for Cerebras
        payload = {
            "model": model,
            "messages": conversations,
            "temperature": ai_temperature,
            "max_completion_tokens": max_tokens,
            "tools": cerebras_compatible_tools
        }
        
        # Make the API call
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        # Check for success
        if response.status_code == 200:
            result = response.json()
            print(result)  # Print full response like OpenAI version
            return result["choices"][0]["message"]
        else:
            print(f"API call failed with status {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"An error occurred during the Cerebras API call: {e}")
        return None

def ensure_object_properties(tools):
    for tool in tools:
        params = tool.get("function", {}).get("parameters", {})
        properties = params.get("properties", {})
        
        for prop_name, prop_def in properties.items():
            if (prop_def.get("type") == "object" and 
                "properties" not in prop_def and 
                "anyOf" not in prop_def):
                # Add empty properties to satisfy Cerebras
                prop_def["properties"] = {}
                #print(f"Fixed {prop_name}: added empty properties")
    
    return tools

def select_cerebras_tools(all_tools):
    """
    Generic function to select tools by name
    
    Args:
        all_tools (list): Complete list of tools
        tool_names (list or set): Names of tools to select
        
    Returns:
        list: Selected tools
    """
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
        "search_and_format_products"
    }
    if isinstance(tool_names, list):
        tool_names = set(tool_names)
    
    selected = []
    
    for tool in all_tools:
        function_name = tool.get("function", {}).get("name")
        if function_name in tool_names:
            selected.append(tool)
    
    print(f"Selected {len(selected)} tools: {[t['function']['name'] for t in selected]}")
    return selected

def serialize_chat_completion_message(message):
    """
    Converts a ChatCompletionMessage object or dict into a serializable dictionary.
    """
    # Handle both object and dict formats
    try:
        # Try object format first
        content = message.content
        role = message.role
        function_call = getattr(message, 'function_call', None)
        tool_calls = getattr(message, 'tool_calls', None)
    except AttributeError:
        # Handle dict format
        if 'choices' in message:
            # Full API response format
            msg_data = message['choices'][0]['message']
        else:
            # Already extracted message
            msg_data = message
            
        content = msg_data.get('content')
        role = msg_data.get('role')
        function_call = msg_data.get('function_call')
        tool_calls = msg_data.get('tool_calls')
    
    message_dict = {
        "content": content,
        "role": role
    }

    # Serialize the function_call if it exists
    if function_call:
        if hasattr(function_call, 'name'):
            # Object format
            message_dict["function_call"] = {
                "name": function_call.name,
                "arguments": function_call.arguments
            }
        else:
            # Dict format
            message_dict["function_call"] = function_call

    # Serialize tool_calls if they exist
    if tool_calls:
        message_dict["tool_calls"] = []
        for tool_call in tool_calls:
            if hasattr(tool_call, 'id'):
                # Object format
                message_dict["tool_calls"].append({
                    "id": tool_call.id,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    },
                    "type": tool_call.type
                })
            else:
                # Dict format - already serialized
                message_dict["tool_calls"].append(tool_call)

    return message_dict


def handle_message_content(response_message, event_type, thread_ts, chat_id, audio_text, source='slack'):
    """
    Handles both text and audio responses from OpenAI.
    Works with both dictionary and ChatCompletionMessage object formats.
    Now supports multiple platforms via MessageRouter.
    
    Args:
        response_message: The OpenAI response message
        event_type: Type of event that triggered the response
        thread_ts: Thread timestamp for threaded conversations
        chat_id: Chat/channel ID where to send the response
        audio_text: Whether this is an audio response
        source: Platform source ('slack', 'telegram', etc.) - defaults to 'slack' for backward compatibility
    """
    
    print(f"Response Message: {response_message}")
    #audio_text = None

    # Check format type
    if isinstance(response_message, dict):
        # Dictionary format
        if "audio" in response_message:
            assistant_reply = response_message["audio"].get("transcript", "")
            audio_file_path = response_message["audio"].get("file_path", "")
            audio_text = assistant_reply
        else:
            assistant_reply = response_message["content"]
    else:
        # ChatCompletionMessage format
        if getattr(response_message, "audio", None):
            assistant_reply = response_message.audio.get("transcript", "")
            audio_file_path = response_message.audio.get("file_path", "")
            audio_text = assistant_reply
        else:
            assistant_reply = response_message.content

    # Save the message
    save_message_weaviate('AssistantMessages', chat_id, assistant_reply, thread_ts)

    # Send the message using MessageRouter if available, otherwise fall back to Slack-only
    if MESSAGE_ROUTER_AVAILABLE:
        try:
            router = get_global_router()
            
            # Determine thread_id based on event type
            thread_id = thread_ts if event_type in ['app_mention', 'New Email'] else None
            
            # Send appropriate message type
            if audio_text:
                router.send_audio(source, chat_id, assistant_reply, thread_id)
            else:
                router.send_message(source, chat_id, assistant_reply, thread_id)
                
            print(f"Message sent via {source} using MessageRouter")
            
        except Exception as e:
            print(f"Error using MessageRouter, falling back to Slack: {e}")
            # Fall back to original Slack-only behavior
            _send_slack_fallback(event_type, thread_ts, chat_id, audio_text, assistant_reply)
    else:
        # Original Slack-only behavior for backward compatibility
        _send_slack_fallback(event_type, thread_ts, chat_id, audio_text, assistant_reply)
    
    return


def _send_slack_fallback(event_type, thread_ts, chat_id, audio_text, assistant_reply):
    """
    Fallback function for Slack-only messaging (preserves original behavior).
    This ensures backward compatibility when MessageRouter is not available.
    """
    if event_type in ['app_mention', 'New Email']:
        if audio_text:
            send_audio_to_slack(assistant_reply, chat_id, thread_ts)
        else:
            send_slack_message(assistant_reply, chat_id, thread_ts)
    else:
        if audio_text:
            send_audio_to_slack(assistant_reply, chat_id, None)
        else:
            send_slack_message(assistant_reply, chat_id, None)

def handle_tool_calls(response_message, available_functions, chat_id, conversations, thread_ts):
    from storage import save_message_weaviate
    
    # Try object format first, fall back to dict format
    try:
        tool_calls = response_message.tool_calls
    except AttributeError:
        # Handle dict format
        if 'tool_calls' in response_message:
            tool_calls = response_message['tool_calls']
        else:
            tool_calls = response_message['choices'][0]['message']['tool_calls']

    response_message_dict = serialize_chat_completion_message(response_message)
    conversations.append(response_message_dict)
    
    def process_tool_call(tool_call):
        try:
            # Handle both object and dict formats
            try:
                # Object format
                function_name = tool_call.function.name
                tool_call_id = tool_call.id
                function_arguments = tool_call.function.arguments
            except AttributeError:
                # Dict format
                function_name = tool_call['function']['name']
                tool_call_id = tool_call['id']
                function_arguments = tool_call['function']['arguments']
            
            function_to_call = available_functions.get(function_name)

            if function_to_call:
                function_args = json.loads(function_arguments)
                function_response = function_to_call(**function_args)
                print(f"Raw Function Response: {function_response}")

                if not isinstance(function_response, str):
                    function_response = json.dumps(function_response, default=decimal_default)
                    print(f"Function Response: {function_response}")
                    if function_name != "google_search" and "odoo" not in function_name:
                        save_message_weaviate('AssistantMessages', chat_id, function_response, thread_ts)
                    
                return {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
        except Exception as e:
            # Handle error logging for both formats
            try:
                tool_call_id = tool_call.id
                function_name = tool_call.function.name
            except AttributeError:
                tool_call_id = tool_call['id']
                function_name = tool_call['function']['name']
                
            logging.error(f"Error processing tool call {tool_call_id}: {str(e)}")
            return {
                "tool_call_id": tool_call_id,
                "role": "tool",
                "name": function_name,
                "content": json.dumps({"error": str(e)}),
            }
        return None

    # Use ThreadPoolExecutor to process tool calls in parallel
    with ThreadPoolExecutor() as executor:
        future_to_tool_call = {executor.submit(process_tool_call, tool_call): tool_call for tool_call in tool_calls}
        
        for future in as_completed(future_to_tool_call):
            tool_call_result = future.result()
            if tool_call_result:
                conversations.append(tool_call_result)

    return conversations