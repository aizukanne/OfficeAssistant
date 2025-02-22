import json
from typing import Dict, List, Optional, Union, Any

def make_text_conversation(
    system_text: str,
    assistant_text: str,
    display_name: str,
    msg_history_summary: List[Dict],
    all_messages: List[Dict],
    text: str
) -> List[Dict]:
    """
    Creates a conversation array for text-based interactions.
    
    Args:
        system_text (str): The system's initial context and instructions
        assistant_text (str): The assistant's role and capabilities
        display_name (str): The user's display name
        msg_history_summary (List[Dict]): Summary of previous message history
        all_messages (List[Dict]): All relevant messages in the conversation
        text (str): The current message text
        
    Returns:
        List[Dict]: The formatted conversation array
    """
    conversation = [
        {"role": "system", "content": system_text},
        {"role": "assistant", "content": assistant_text}
    ]

    conversation.append({
        "role": "assistant",
        "content": json.dumps(msg_history_summary, default=decimal_default)
    })

    for message in all_messages:
        conversation.append({
            "role": message['role'],
            "content": message['message']
        })

    conversation.append({
        "role": "assistant",
        "content": "All the previous messages are a trail of the message history to aid your understanding of the conversation. The next message is the current request from the user."
    })

    if display_name:
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

def make_vision_conversation(
    system_text: str,
    assistant_text: str,
    display_name: str,
    msg_history_summary: List[Dict],
    all_messages: List[Dict],
    text: str,
    image_urls: Optional[List[str]] = None
) -> List[Dict]:
    """
    Creates a conversation array for vision-based interactions.
    
    Args:
        system_text (str): The system's initial context and instructions
        assistant_text (str): The assistant's role and capabilities
        display_name (str): The user's display name
        msg_history_summary (List[Dict]): Summary of previous message history
        all_messages (List[Dict]): All relevant messages in the conversation
        text (str): The current message text
        image_urls (Optional[List[str]]): List of image URLs to include
        
    Returns:
        List[Dict]: The formatted conversation array
    """
    conversation = [
        {"role": "system", "content": [{"type": "text", "text": system_text}]},
        {"role": "assistant", "content": [{"type": "text", "text": assistant_text}]}
    ]

    conversation.append({
        "role": "assistant",
        "content": [{"type": "text", "text": json.dumps(msg_history_summary, default=decimal_default)}]
    })

    for message in all_messages:
        content = [{"type": "text", "text": message['message']}]
        
        if "image_urls" in message:
            for url in message["image_urls"]:
                if url:  # Ensure the URL is not empty
                    content.append({"type": "image_url", "image_url": {"url": url}})
        
        conversation.append({
            "role": message['role'],
            "content": content
        })

    conversation.append({
        "role": "assistant",
        "content": "All the previous messages are a trail of the message history to aid your understanding of the conversation. The next message is the current request from the user."
    })

    user_content = [{"type": "text", "text": text}]

    if image_urls is not None:
        for url in image_urls:
            if url:  # Check if the URL is not empty
                user_content.append({"type": "image_url", "image_url": {"url": url}})

    if display_name:
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

def make_audio_conversation(
    system_text: str,
    assistant_text: str,
    display_name: str,
    msg_history_summary: List[Dict],
    all_messages: List[Dict],
    text: str,
    audio_urls: Optional[List[str]] = None
) -> List[Dict]:
    """
    Creates a conversation array for audio-based interactions.
    
    Args:
        system_text (str): The system's initial context and instructions
        assistant_text (str): The assistant's role and capabilities
        display_name (str): The user's display name
        msg_history_summary (List[Dict]): Summary of previous message history
        all_messages (List[Dict]): All relevant messages in the conversation
        text (str): The current message text
        audio_urls (Optional[List[str]]): List of audio URLs to include
        
    Returns:
        List[Dict]: The formatted conversation array
    """
    conversation = [
        {"role": "system", "content": [{"type": "text", "text": system_text}]},
        {"role": "assistant", "content": [{"type": "text", "text": assistant_text}]},
    ]

    conversation.append({
        "role": "assistant",
        "content": [{"type": "text", "text": json.dumps(msg_history_summary)}],
    })

    for message in all_messages:
        content = [{"type": "text", "text": message["message"]}]
        conversation.append({
            "role": message["role"],
            "content": content,
        })

    conversation.append({
        "role": "assistant",
        "content": "All the previous messages are a trail of the message history to aid your understanding of the conversation. The next message is the current request from the user.",
    })

    user_content = [{"type": "text", "text": text}]
    if audio_urls is not None:
        for url in audio_urls:
            if url:
                response = requests.get(url)
                response.raise_for_status()
                m4a_data = response.content
                wav_data = convert_to_wav_in_memory(m4a_data)
                encoded_string = base64.b64encode(wav_data).decode("utf-8")
                user_content.append({
                    "type": "input_audio",
                    "input_audio": {
                        "data": encoded_string,
                        "format": "wav"
                    }
                })

    if display_name:
        conversation.append({
            "role": "user",
            "content": user_content,
            "name": display_name,
        })
    else:
        conversation.append({
            "role": "user",
            "content": user_content,
        })

    print(f"Conversation: {json.dumps(conversation)}")
    return conversation

def handle_message_content(
    response_message: Union[Dict, Any],
    event_type: str,
    thread_ts: str,
    chat_id: str
) -> None:
    """
    Handles both text and audio responses from OpenAI.
    Works with both dictionary and ChatCompletionMessage object formats.
    
    Args:
        response_message: The response message from OpenAI
        event_type: The type of event being handled
        thread_ts: The thread timestamp
        chat_id: The chat ID
    """
    global audio_text
    print(f"Response Message: {response_message}")

    # Check format type
    if isinstance(response_message, dict):
        if "audio" in response_message:
            assistant_reply = response_message["audio"].get("transcript", "")
            audio_file_path = response_message["audio"].get("file_path", "")
            audio_text = assistant_reply
        else:
            assistant_reply = response_message["content"]
    else:
        if getattr(response_message, "audio", None):
            assistant_reply = response_message.audio.get("transcript", "")
            audio_file_path = response_message.audio.get("file_path", "")
            audio_text = assistant_reply
        else:
            assistant_reply = response_message.content

    save_message(assistant_table, chat_id, assistant_reply, "assistant", thread_ts)

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

def handle_tool_calls(
    response_message: Any,
    available_functions: Dict,
    chat_id: str,
    conversations: List[Dict],
    thread_ts: str
) -> List[Dict]:
    """
    Handles tool calls from the OpenAI response.
    
    Args:
        response_message: The response message containing tool calls
        available_functions: Dictionary of available functions
        chat_id: The chat ID
        conversations: The current conversation history
        thread_ts: The thread timestamp
        
    Returns:
        List[Dict]: Updated conversations with tool responses
    """
    tool_calls = response_message.tool_calls

    response_message_dict = serialize_chat_completion_message(response_message)
    conversations.append(response_message_dict)

    def process_tool_call(tool_call):
        try:
            function_name = tool_call.function.name
            function_to_call = available_functions.get(function_name)

            if function_to_call:
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)

                if not isinstance(function_response, str):
                    function_response = json.dumps(function_response, default=decimal_default)
                    print(f"Function Response: {function_response}")
                    if function_name != "google_search":
                        save_message(assistant_table, chat_id, function_response, "assistant", thread_ts)

                return {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
        except Exception as e:
            logging.error(f"Error processing tool call {tool_call.id}: {str(e)}")
            return {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": json.dumps({"error": str(e)}),
            }
        return None

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_tool_call = {executor.submit(process_tool_call, tool_call): tool_call for tool_call in tool_calls}
        
        for future in concurrent.futures.as_completed(future_to_tool_call):
            tool_call_result = future.result()
            if tool_call_result:
                conversations.append(tool_call_result)

    return conversations