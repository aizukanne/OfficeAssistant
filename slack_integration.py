import json
import os
import re
import requests
import tempfile
import markdown2
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
from config import slack_bot_token, names_table, channels_table, image_bucket_name

from storage import (
    get_users, get_channels
)

from media_processing import transcribe_multiple_urls, download_and_read_file, upload_image_to_s3
from prompts import prompts

def convert_markdown_to_slack(content):
    # Convert bold text
    content = re.sub(r"\*\*(.*?)\*\*", r"*\1*", content)

    # Convert italic text
    content = re.sub(r"\_(.*?)\_", r"_\1_", content)

    # Convert LaTeX (or similar) to Slack code format
    content = re.sub(r"\\\( (.*?) \\\)", r"`\1`", content)

    return content

def convert_to_slack_blocks(markdown_text):
    lines = markdown_text.split('\n')
    blocks = []
    current_section = []
    in_code_block = False
    in_blockquote = False

    def clean_heading_text(text):
        """Helper function to clean heading text by removing leading/trailing whitespace and asterisks"""
        text = text.strip()  # Remove whitespace
        # Remove leading/trailing asterisks
        while text.startswith('*') and text.endswith('*'):
            text = text[1:-1].strip()
        return text

    for line in lines:
        if in_code_block:
            # Check for the end of the code block
            if line.startswith("```"):
                # Add the current code block as a section
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "```\n" + "\n".join(current_section) + "\n```",
                    }
                })
                current_section = []
                in_code_block = False
            else:
                # If we're inside a code block, append the line without modifying it
                current_section.append(line)
            continue
        
        # Handle horizontal rules
        if line.strip() in ('***', '---', '___'):
            if current_section:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n".join(current_section)
                    }
                })
                current_section = []
            blocks.append({"type": "divider"})
            continue
        
        # Handle the start of a code block
        if line.startswith("```"):
            # Flush any current text as a section
            if current_section:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n".join(current_section)
                    }
                })
                current_section = []
            in_code_block = True
            current_section.append(line)  # Include the starting backticks
            continue
        
        # Replace Markdown bold with Slack's bold syntax outside code blocks
        line = line.replace('**', '*')

        # Handle blockquotes
        if line.startswith('>'):
            if not in_blockquote:
                in_blockquote = True
                if current_section:
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "\n".join(current_section)
                        }
                    })
                    current_section = []
            current_section.append(line[1:].strip())  # Remove '>' and add line
        elif in_blockquote and not line.startswith('>'):
            # End of blockquote
            in_blockquote = False
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "\n".join(current_section)
                }
            })
            current_section = []

        # Headers and regular text
        elif line.lstrip().startswith('#'):
            if current_section:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n".join(current_section)
                    }
                })
                current_section = []
            
            # Count the number of # symbols and remove them
            heading_level = 0
            line_stripped = line.lstrip()
            for char in line_stripped:
                if char == '#':
                    heading_level += 1
                else:
                    break
            
            # Extract the heading text, remove leading/trailing whitespace and asterisks
            heading_text = clean_heading_text(line_stripped[heading_level:])
            
            # Use progressively smaller markers as the heading level increases
            size_markers = ['◆', '🔷', '🔹', '▪️', '▫️', '·']  # For H1 through H6
            marker = size_markers[min(heading_level - 1, len(size_markers) - 1)]
            
            # All headings are now section blocks with bold text
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{marker} *{heading_text}*"
                }
            })
        elif line.strip():
            current_section.append(line)

        # Empty lines and end of blockquotes
        elif current_section:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "\n".join(current_section)
                }
            })
            current_section = []
            in_blockquote = False

    # Add the last section if there is any text left
    if current_section:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n".join(current_section)
            }
        })

    return json.dumps(blocks)

def send_slack_message(message, channel, ts=None):
    # Slack Bot URL
    url = "https://slack.com/api/chat.postMessage"

    text_message = BeautifulSoup(markdown2.markdown(message), 'html.parser').get_text()
    slack_blocks = convert_to_slack_blocks(message)
    
    # Message data
    data = {
        'channel': channel,
        'text': message,
        'thread_ts': ts,
        'blocks': slack_blocks
    }
    
    # HTTP headers
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': 'Bearer ' + slack_bot_token
    }

    response = requests.post(url, headers=headers, json=data)

    return response.json()

def send_audio_to_slack(text, chat_id=None, ts=None):
    """
    Converts text to speech and uploads the audio file to Slack using the external upload API.
    
    Parameters:
    - text: The text to be converted to speech
    - chat_id: The ID of the Slack channel where the file will be uploaded (optional)
    - ts: Thread timestamp to attach the file to (optional)
    
    Returns:
    - dict: The JSON response from the files.completeUploadExternal API
    """
    from media_processing import text_to_speech
    
    # Convert text to speech and get file details
    file_path = text_to_speech(text, file_suffix=".mp3")
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    
    # Step 1: Get upload URL
    headers = {
        "Authorization": f"Bearer {slack_bot_token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    url_params = {
        "filename": file_name,
        "length": file_size
    }
    
    response = requests.get(
        "https://slack.com/api/files.getUploadURLExternal",
        headers=headers,
        params=url_params
    )
    
    if not response.ok or not response.json().get("ok"):
        error = response.json().get("error", "Unknown error")
        print(f"Error getting upload URL: {error}")
        return response.json()
    
    upload_url = response.json()["upload_url"]
    file_id = response.json()["file_id"]
    
    # Step 2: Upload file to the provided URL
    with open(file_path, "rb") as file:
        files = {
            "file": (file_name, file, "audio/mpeg")
        }
        upload_response = requests.post(upload_url, files=files)
    
    if not upload_response.ok:
        print(f"Error uploading file: {upload_response.status_code}")
        return {"ok": False, "error": "upload_failed"}
    
    # Step 3: Complete the upload
    complete_data = {
        "files": [{
            "id": file_id,
            "title": "Audio Response"
        }]
    }
    
    # Add optional parameters if provided
    if chat_id:
        complete_data["channel_id"] = chat_id
    if ts:
        complete_data["thread_ts"] = ts
    
    complete_response = requests.post(
        "https://slack.com/api/files.completeUploadExternal",
        headers={
            "Authorization": f"Bearer {slack_bot_token}",
            "Content-Type": "application/json"
        },
        json=complete_data
    )
    
    if complete_response.ok and complete_response.json().get("ok"):
        print(f"File uploaded successfully: {file_id}")
    else:
        error = complete_response.json().get("error", "Unknown error")
        print(f"Error completing upload: {error}")
    
    return complete_response.json()

def send_file_to_slack(file_path, chat_id, title, ts=None):
    """
    Uploads a file to a specified Slack channel using the external upload API.
    If the file_path is a URL, downloads the file first.
    
    Parameters:
    - file_path: The path to the file or a URL
    - chat_id: The ID of the Slack channel where the file will be uploaded
    - title: The title of the file
    - ts: The thread timestamp (optional)
    
    Returns:
    - dict: The JSON response from the files.completeUploadExternal API
    """
    # Check if file_path is a URL
    parsed_url = urlparse(file_path)
    is_url = parsed_url.scheme in ('http', 'https')
    
    if is_url:
        # Download the file into a temporary file
        response = requests.get(file_path)
        response.raise_for_status()  # Ensure the download succeeded
        suffix = os.path.splitext(parsed_url.path)[1]  # Extract the file extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(response.content)
            file_to_upload = tmp_file.name
    else:
        file_to_upload = file_path

    try:
        # Get file details
        file_size = os.path.getsize(file_to_upload)
        file_name = os.path.basename(file_to_upload)
        
        # Step 1: Get upload URL
        headers = {
            "Authorization": f"Bearer {slack_bot_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        url_params = {
            "filename": file_name,
            "length": file_size
        }
        
        response = requests.get(
            "https://slack.com/api/files.getUploadURLExternal",
            headers=headers,
            params=url_params
        )
        
        if not response.ok or not response.json().get("ok"):
            error = response.json().get("error", "Unknown error")
            print(f"Error getting upload URL: {error}")
            return response.json()
        
        upload_url = response.json()["upload_url"]
        file_id = response.json()["file_id"]
        
        # Step 2: Upload file to the provided URL
        with open(file_to_upload, "rb") as file:
            # Determine content type based on file extension
            import mimetypes
            file_extension = os.path.splitext(file_to_upload)[1].lower()
            content_type = mimetypes.guess_type(file_to_upload)[0] or "application/octet-stream"
            
            files = {
                "file": (file_name, file, content_type)
            }
            upload_response = requests.post(upload_url, files=files)
        
        if not upload_response.ok:
            print(f"Error uploading file: {upload_response.status_code}")
            return {"ok": False, "error": "upload_failed"}
        
        # Step 3: Complete the upload
        complete_data = {
            "files": [{
                "id": file_id,
                "title": title
            }],
            "channel_id": chat_id
        }
        
        if ts:
            complete_data["thread_ts"] = ts
        
        complete_response = requests.post(
            "https://slack.com/api/files.completeUploadExternal",
            headers={
                "Authorization": f"Bearer {slack_bot_token}",
                "Content-Type": "application/json"
            },
            json=complete_data
        )
        
        if complete_response.ok and complete_response.json().get("ok"):
            print(f"File uploaded successfully: {file_id}")
        else:
            error = complete_response.json().get("error", "Unknown error")
            print(f"Error completing upload: {error}")
        
        return complete_response.json()
        
    finally:
        if is_url:
            # Remove the temporary file
            os.unlink(file_to_upload)

def update_slack_users():
    url = 'https://slack.com/api/users.list'
    headers = {
        'Authorization': f'Bearer {slack_bot_token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        users_list = response.json().get('members', [])
        for user in users_list:
            if not user.get('deleted', True) and not user.get('is_bot', True) and not user.get('is_app_user', True):
                user_id = user.get('id')
                try:
                    response = names_table.get_item(Key={'user_id': user_id})
                    item = response.get('Item', None)
                    if item:
                        print(f"User {user_id} already exists in the database.")
                        # Check if all keys are available
                        missing_keys = [key for key in ['real_name', 'display_name', 'email'] if key not in item]
                        if missing_keys:
                            print(f"Updating user {user_id} with missing keys: {missing_keys}")
                            for key in missing_keys:
                                item[key] = user.get('profile', {}).get(key, '')
                            names_table.put_item(Item=item)
                            print(f"User {user_id} updated successfully.")
                    else:
                        print(f"Adding user {user_id} to the database.")
                        user_data = {
                            'user_id': user_id,
                            'real_name': user.get('profile', {}).get('real_name', ''),
                            'display_name': user.get('profile', {}).get('display_name', ''),
                            'email': user.get('profile', {}).get('email', '')
                        }
                        names_table.put_item(Item=user_data)
                        print(f"User {user_id} added successfully.")
                except Exception as e:
                    print(f"Error processing user {user_id}: {e}")
    else:
        print(f"Failed to retrieve users list: HTTP {response.status_code}")

def update_slack_conversations():
    url = 'https://slack.com/api/conversations.list'
    headers = {
        'Authorization': f'Bearer {slack_bot_token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    params = {
        'types': 'public_channel,private_channel'
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        conversations_list = response.json().get('channels', [])
        for channel in conversations_list:
            channel_id = channel.get('id')
            try:
                # Retrieve the existing channel details from DynamoDB 
                existing_channel = channels_table.get_item(Key={'id': channel_id})
                
                if 'Item' in existing_channel:
                    print(f"Channel {channel_id} already exists in the database.")
                    # Existing channel: update if necessary
                    channels_table.update_item(
                        Key={'id': channel_id},
                        UpdateExpression="set #info.#name=:n, #info.#is_private=:p, #info.#num_members=:m",
                        ExpressionAttributeValues={
                            ':n': channel.get('name'),
                            ':p': channel.get('is_private'),
                            ':m': channel.get('num_members')
                        },
                        ExpressionAttributeNames={
                            "#info": "info",
                            "#name": "name",  # Using an expression attribute name as a placeholder
                            "#is_private": "is_private",
                            "#num_members": "num_members"
                        }
                    )
                else:
                    # New channel: add to the database      
                    channels_table.put_item(Item=channel)
                    print(f"Channel {channel_id} added to the database.")

            except Exception as e:
                print(f"Error updating channel {channel_id}: {e}")
    else:
        print(f"Failed to retrieve conversations list: HTTP {response.status_code}")

def get_slack_user_name(user_id):
    """
    Function to get the name of the user who sent a message in Slack.
    
    Parameters: 
    user_id (str): The user ID of the message sender.
    
    Returns:
    str: The real name of the user if found, otherwise an error message.
    """
    url = 'https://slack.com/api/users.info'
    headers = {
        'Authorization': f'Bearer {slack_bot_token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    params = {
        'user': user_id
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        user_info = response.json()
        if user_info.get('ok'):
            # Extracting the user's real name from the response
            user_name = user_info['user']['profile']['real_name']
            display_name = user_info['user']['profile']['display_name']
            email = user_info['user']['profile']['email']
            return {"User Name": user_name, "Display Name": display_name, "Email": email}
        else:
            # Return the error message if the 'ok' field is False
            return user_info.get('error', 'Unknown error occurred')
    else:
        return f'HTTP Error: {response.status_code}'

def latex_to_slack(latex_str):
    """
    Convert a LaTeX string to a Slack-friendly format.      
    
    Args:
    latex_str (str): A string containing LaTeX commands. 

    Returns:
    str: A string formatted for Slack.
    """
    # Replace common LaTeX commands with Slack-friendly equivalents     
    replacements = {
        '\\times': '×',  # Multiplication
        '\\frac': '/',   # Fractions
        '\\sqrt': '√',   # Square root
        '^': '**',       # Exponentiation
        '_': '~'         # Subscript
    }

    slack_str = latex_str
    for latex, slack in replacements.items():
        slack_str = slack_str.replace(latex, slack)

    return slack_str

def message_to_json(message_string):
    message_parts = re.split(r'```json|```', message_string)
    
    message = {
        "assistant": f"{message_parts[0].strip()} {message_parts[2].strip()}",
        "blocks": json.loads(message_parts[1])['blocks']
    }
    
    return json.dumps(message)

def find_image_urls(data):
    """
    Extracts image URLs from message data.
    
    Args:
        data (list): List of message data dictionaries
        
    Returns:
        tuple: (bool, list) indicating if URLs were found and the list of URLs
    """
    image_urls = []  # Initialize an empty list to hold all image URLs
    for item in data:
        if "image_urls" in item:
            # Extend the list of image_urls with the URLs found in the current item
            image_urls.extend(item["image_urls"])
    # Return True if the list is not empty (indicating that at least one URL was found),
    # and the list of all found image URLs
    return bool(image_urls), image_urls


def process_slack_event(slack_event):
    """Process Slack event and return standardized parameters"""
    try:
        event_data = slack_event['event']
        event_type = event_data['type']
        
        # Initialize return parameters
        chat_id = event_data['channel']
        thread_ts = event_data.get('thread_ts', event_data['ts'])
        
        # Check if the 'user' key exists and has a value 
        if 'user' in event_data and event_data['user']:
            user_id = event_data['user']
        else:
            # Return None to indicate this should be ignored
            return None
        
        # Ignore messages from the bot itself  
        if 'bot_id' in event_data:
            return None
        
        # Retrieve the name of the user         
        user = get_users(user_id)
        user_name = user['real_name']
        display_name = user['display_name']
        display_name = display_name.replace(' ', '_').replace('.', '').strip()
        
        # Get message text
        try:
            text = event_data['text']
        except KeyError:
            print(f"An error occurred. No text found. event_data: {json.dumps(event_data)}")
            text = ""
        
        # Process images
        image_urls = []
        try:
            for file in event_data["files"]:
                if file["mimetype"].startswith("image/"):
                    image_url = file["url_private"]
                    uploaded_url = upload_image_to_s3(image_url, image_bucket_name)
                    image_urls.append(uploaded_url)
        except KeyError:
            image_urls = []
        
        # Process audio
        audio_urls = []
        audio_text = []
        try:
            for file in event_data["files"]:
                if file["mimetype"].startswith(("audio/", "video/")):
                    audio_url = file["url_private"]
                    audio_urls.append(audio_url)

            if audio_urls:
                audio_text = transcribe_multiple_urls(audio_urls, platform='slack')
                if audio_text:
                    speech_instruction = prompts['speech_instruction']
                    audio_text.append(speech_instruction)
        except KeyError:
            audio_urls = []
            audio_text = []
        
        # Process documents
        size_limit_mb = 5
        application_files = []
        try:
            for file in event_data["files"]:
                if file["mimetype"].startswith("application/") or file["mimetype"].startswith("text/"):
                    file_url = file["url_private"]
                    file_name = file.get("name", "Unnamed File")
                    file_size_mb = file.get("size", 1) / (1024 * 1024)
                    if file_size_mb > size_limit_mb:
                        application_files.append({
                            "file_name": file_name, 
                            "content": f"File {file_name} is over the {size_limit_mb} MB limit. URL: {file_url}"
                        })
                    else:
                        file_content = download_and_read_file(file_url, file["mimetype"], platform='slack')
                        application_files.append({
                            "Message": "The user sent a file with this message. The contents of the file have been appended to this message.", 
                            "Filename": file_name, 
                            "content": file_content
                        })
        except KeyError:
            application_files = []
        
        # Check for attachments (forwarded messages)
        if 'attachments' in event_data:
            attachments = event_data['attachments']
            for attachment in attachments:
                if 'text' in attachment:
                    forwarded_message_text = attachment['text']
                    text += f"\n\nForwarded Message:\n{forwarded_message_text}"
        
        return {
            'chat_id': chat_id,
            'user_id': user_id,
            'user_name': user_name,
            'display_name': display_name,
            'text': text,
            'thread_ts': thread_ts,
            'image_urls': image_urls,
            'audio_urls': audio_urls,
            'audio_text': audio_text,
            'application_files': application_files,
            'event_type': event_type
        }
        
    except Exception as e:
        print(f"Error processing Slack event: {e}")
        return None