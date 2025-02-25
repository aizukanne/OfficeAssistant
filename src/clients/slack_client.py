import os
import json
import requests
import tempfile
import markdown2
import mimetypes
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
from io import BytesIO

# Initialize Slack token from environment
slack_bot_token = os.getenv('SLACK_BOT_TOKEN')

def send_slack_message(message, channel, ts=None):
    # Slack Bot URL
    url = "https://slack.com/api/chat.postMessage"

    text_message = BeautifulSoup(markdown2.markdown(message), 'html.parser').get_text()
    slack_blocks = convert_to_slack_blocks(message)
    print(f"Slack Blocks: {slack_blocks}") 
    
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
        'Authorization': f'Bearer {slack_bot_token}'
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
    # Use the global chat_id if it's not passed as an argument
    if chat_id is None:
        chat_id = globals()['chat_id']
    
    # Convert text to speech and get file details
    file_path = text_to_speech(text, file_suffix=".mp3")  # This will need to be imported from openai_client
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