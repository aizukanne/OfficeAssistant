import json
import os
import requests
from typing import Dict, Optional, Any, List

# Initialize Slack token
slack_bot_token = os.getenv('SLACK_BOT_TOKEN')

def send_slack_message(
    message: str,
    channel: str,
    thread_ts: Optional[str] = None
) -> Dict:
    """
    Sends a message to a Slack channel.
    
    Args:
        message: The message to send
        channel: The channel to send to
        thread_ts: Optional thread timestamp for threaded replies
        
    Returns:
        Dict: The response from Slack API
    """
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {slack_bot_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "channel": channel,
        "text": message,
        "unfurl_links": True,
        "unfurl_media": True
    }
    
    if thread_ts:
        data["thread_ts"] = thread_ts
        
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error sending Slack message: {e}")
        return {"ok": False, "error": str(e)}

def send_audio_to_slack(
    text: str,
    chat_id: str,
    thread_ts: Optional[str] = None
) -> Dict:
    """
    Sends an audio message to Slack.
    
    Args:
        text: The text to convert to audio
        chat_id: The channel ID
        thread_ts: Optional thread timestamp
        
    Returns:
        Dict: The response from Slack API
    """
    # This is a placeholder - actual implementation would need to:
    # 1. Convert text to audio using a TTS service
    # 2. Upload the audio file to Slack
    # 3. Send a message with the audio attachment
    return send_slack_message(text, chat_id, thread_ts)

def send_file_to_slack(
    file_path: str,
    chat_id: str,
    title: str,
    thread_ts: Optional[str] = None
) -> Dict:
    """
    Uploads a file to Slack.
    
    Args:
        file_path: Path to the file to upload
        chat_id: The channel ID
        title: Title for the file
        thread_ts: Optional thread timestamp
        
    Returns:
        Dict: The response from Slack API
    """
    url = "https://slack.com/api/files.upload"
    headers = {
        "Authorization": f"Bearer {slack_bot_token}"
    }
    
    with open(file_path, 'rb') as file:
        data = {
            "channels": chat_id,
            "title": title,
            "filename": os.path.basename(file_path)
        }
        
        if thread_ts:
            data["thread_ts"] = thread_ts
            
        files = {
            'file': file
        }
        
        try:
            response = requests.post(url, headers=headers, data=data, files=files)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error uploading file to Slack: {e}")
            return {"ok": False, "error": str(e)}

def send_as_pdf(
    text: str,
    chat_id: str,
    title: str,
    thread_ts: Optional[str] = None
) -> Dict:
    """
    Converts text to PDF and sends it to Slack.
    
    Args:
        text: The text to convert to PDF
        chat_id: The channel ID
        title: Title for the PDF
        thread_ts: Optional thread timestamp
        
    Returns:
        Dict: The response from Slack API
    """
    # This is a placeholder - actual implementation would need to:
    # 1. Convert text to PDF
    # 2. Save PDF temporarily
    # 3. Upload PDF to Slack
    # 4. Clean up temporary file
    return send_slack_message(text, chat_id, thread_ts)

def get_users(user_id: Optional[str] = None) -> Dict:
    """
    Retrieves user information from Slack.
    
    Args:
        user_id: Optional specific user ID to retrieve
        
    Returns:
        Dict: User information
    """
    if user_id:
        url = "https://slack.com/api/users.info"
        params = {"user": user_id}
    else:
        url = "https://slack.com/api/users.list"
        params = {}
        
    headers = {
        "Authorization": f"Bearer {slack_bot_token}"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting Slack users: {e}")
        return {"ok": False, "error": str(e)}

def get_channels(channel_id: Optional[str] = None) -> Dict:
    """
    Retrieves channel information from Slack.
    
    Args:
        channel_id: Optional specific channel ID to retrieve
        
    Returns:
        Dict: Channel information
    """
    if channel_id:
        url = "https://slack.com/api/conversations.info"
        params = {"channel": channel_id}
    else:
        url = "https://slack.com/api/conversations.list"
        params = {"types": "public_channel,private_channel"}
        
    headers = {
        "Authorization": f"Bearer {slack_bot_token}"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting Slack channels: {e}")
        return {"ok": False, "error": str(e)}

def manage_mute_status(status: Optional[bool] = None) -> List[bool]:
    """
    Manages the mute status for the bot.
    
    Args:
        status: Optional boolean to set the mute status
        
    Returns:
        List[bool]: Current mute status
    """
    # This is a placeholder - actual implementation would need to:
    # 1. Store mute status in a persistent storage
    # 2. Retrieve or update the status as needed
    return [False]  # Default to unmuted

def upload_image_to_s3(
    image_url: str,
    bucket_name: str
) -> Optional[str]:
    """
    Downloads an image from Slack and uploads it to S3.
    
    Args:
        image_url: The Slack image URL
        bucket_name: The S3 bucket name
        
    Returns:
        Optional[str]: The S3 URL if successful, None otherwise
    """
    headers = {
        "Authorization": f"Bearer {slack_bot_token}"
    }
    
    try:
        # Download image from Slack
        response = requests.get(image_url, headers=headers)
        response.raise_for_status()
        
        # Generate unique filename
        filename = f"image_{int(time.time())}.jpg"
        
        # Upload to S3
        s3_client = boto3.client('s3')
        s3_client.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=response.content,
            ContentType=response.headers.get('content-type', 'image/jpeg')
        )
        
        return f"https://{bucket_name}.s3.amazonaws.com/{filename}"
    except Exception as e:
        print(f"Error uploading image to S3: {e}")
        return None