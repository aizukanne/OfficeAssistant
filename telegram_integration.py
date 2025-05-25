import re
import time
import requests
import tempfile
import base64

from config import telegram_bot_token

from storage import (
    get_users, get_channels
)

# Import media processing functions if available
try:
    from media_processing import text_to_speech, transcribe_multiple_urls, download_and_read_file
    from prompts import prompts
except ImportError:
    def text_to_speech(text):
        raise NotImplementedError("Text-to-speech functionality not available")
    
    def transcribe_multiple_urls(urls, platform='slack'):
        raise NotImplementedError("Audio transcription functionality not available")
    
    def download_and_read_file(url, content_type, platform='slack'):
        raise NotImplementedError("File download functionality not available")
    
    prompts = {'speech_instruction': 'Audio transcription:'}


def process_telegram_event(telegram_event):
    """Process Telegram event and return standardized parameters"""
    try:
        message = telegram_event['message']
        event_type = 'message'  # Telegram equivalent
        
        # Extract chatId and text from the incoming message
        chat_id = str(message['chat']['id'])  # Convert to string for consistency with Slack
        
        if 'text' in message:
            text = str(message['text'])
        else:
            text = "Smiley"  # or some default value
        
        # Extract the sender's first_name, clean it up and use it as user name
        user_name = message['from'].get('first_name', '')
        # If first_name starts with '@', remove it
        if user_name.startswith('@'):
            user_name = user_name[1:]
        # Remove any non-alphabetical characters
        user_name = re.sub(r'[^a-zA-Z]', '', user_name)
        # If name is null or empty, replace with "Stranger!"
        if not user_name:
            user_name = "Stranger!"
        
        # For Telegram, we'll use user_name as display_name and user_id
        user_id = str(message['from']['id'])
        display_name = user_name
        
        # Generate thread_ts equivalent (Telegram doesn't have threads, so use message timestamp)
        thread_ts = str(message.get('date', time.time()))
        
        # Initialize lists for media processing
        image_urls = []
        audio_urls = []
        audio_text = []
        application_files = []
        
        # Process photos
        if 'photo' in message:
            # Telegram sends photos as an array of different sizes
            # Get the largest photo (last in the array)
            largest_photo = message['photo'][-1]
            file_id = largest_photo['file_id']
            
            # Get file URL from Telegram
            file_url = get_telegram_file_url(file_id)
            if file_url:
                image_urls.append(file_url)
                if not text:
                    text = "Photo shared"
        
        # Process audio files
        if 'audio' in message:
            file_id = message['audio']['file_id']
            file_url = get_telegram_file_url(file_id)
            if file_url:
                audio_urls.append(file_url)
                if not text:
                    text = "Audio file shared"
        
        # Process voice messages
        if 'voice' in message:
            file_id = message['voice']['file_id']
            file_url = get_telegram_file_url(file_id)
            if file_url:
                audio_urls.append(file_url)
                if not text:
                    text = "Voice message"
        
        # Transcribe audio if we have audio URLs
        if audio_urls:
            try:
                audio_text = transcribe_multiple_urls(audio_urls, platform='telegram')
                if audio_text:
                    # Add speech instruction to help AI understand this is transcribed audio
                    speech_instruction = prompts.get('speech_instruction', 'Audio transcription:')
                    audio_text.append(speech_instruction)
                    print(f"Telegram audio transcribed: {audio_text}")
            except Exception as e:
                print(f"Error transcribing Telegram audio: {e}")
                audio_text = []
        
        # Process documents
        if 'document' in message:
            file_id = message['document']['file_id']
            filename = message['document'].get('file_name', 'document')
            file_size = message['document'].get('file_size', 0)
            mime_type = message['document'].get('mime_type', 'application/octet-stream')
            file_url = get_telegram_file_url(file_id)
            
            if file_url:
                # Apply size limit (5MB)
                size_limit_mb = 5
                file_size_mb = file_size / (1024 * 1024)
                
                if file_size_mb > size_limit_mb:
                    application_files.append({
                        "file_name": filename,
                        "content": f"File {filename} is over the {size_limit_mb} MB limit. Size: {file_size_mb:.2f} MB"
                    })
                else:
                    try:
                        # Only process text-based files that we can read
                        if mime_type.startswith("application/") or mime_type.startswith("text/"):
                            file_content = download_and_read_file(file_url, mime_type, platform='telegram')
                            application_files.append({
                                "Message": "The user sent a file with this message. The contents of the file have been appended to this message.",
                                "Filename": filename,
                                "content": file_content
                            })
                        else:
                            # For non-text files, just record the filename and type
                            application_files.append({
                                "file_name": filename,
                                "content": f"File {filename} ({mime_type}) was shared but content cannot be read."
                            })
                    except Exception as e:
                        print(f"Error processing Telegram document {filename}: {e}")
                        application_files.append({
                            "file_name": filename,
                            "content": f"Error reading file {filename}: {str(e)}"
                        })
                
                if not text:
                    text = f"Document shared: {filename}"
        
        # If we have a caption from media, use it as text
        if 'caption' in message and message['caption']:
            text = message['caption']
        
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
        print(f"Error processing Telegram event: {e}")
        return None



def send_telegram_message(chat_id, message):
   
    url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    
    def convert_markdown_to_html(text):
        #Convert markdown formatting to HTML
        # First escape HTML characters to prevent injection
        escaped = html.escape(text)
        
        # Convert markdown-style formatting to HTML
        # **bold** -> <b>bold</b>
        escaped = re.sub(r'\*\*([^*\n]+?)\*\*', r'<b>\1</b>', escaped)
        
        # *italic* -> <i>italic</i> (avoid conflicts with bold)
        escaped = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<i>\1</i>', escaped)
        
        # `code` -> <code>code</code>
        escaped = re.sub(r'`([^`\n]+?)`', r'<code>\1</code>', escaped)
        
        # __underline__ -> <u>underline</u>
        escaped = re.sub(r'__([^_\n]+?)__', r'<u>\1</u>', escaped)
        
        # ~~strikethrough~~ -> <s>strikethrough</s>
        escaped = re.sub(r'~~([^~\n]+?)~~', r'<s>\1</s>', escaped)
        
        return escaped
    
    def split_message(text, max_length=4096):
        """Split long messages at natural break points"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        lines = text.split('\n')
        current_chunk = ""
        
        for line in lines:
            if len(current_chunk) + len(line) + 1 > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = line
                else:
                    # Single line too long, split by words
                    words = line.split(' ')
                    for word in words:
                        if len(current_chunk) + len(word) + 1 > max_length:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                current_chunk = word
                            else:
                                # Single word too long, just add it
                                chunks.append(word)
                        else:
                            current_chunk = current_chunk + ' ' + word if current_chunk else word
            else:
                current_chunk = current_chunk + '\n' + line if current_chunk else line
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    # Convert markdown to HTML
    formatted_message = convert_markdown_to_html(message)
    
    # Split if message is too long
    chunks = split_message(formatted_message)
    
    results = []
    for i, chunk in enumerate(chunks):
        data = {
            'chat_id': chat_id,
            'text': chunk,
            'parse_mode': 'HTML'
        }
        
        # Try with HTML formatting first
        response = requests.post(url, data=data)
        result = response.json()
        
        # If HTML parsing fails, try without formatting
        if not result.get('ok') and 'parse' in result.get('description', '').lower():
            print(f"HTML parsing failed, sending without formatting: {result.get('description', '')}")
            data['parse_mode'] = None
            data['text'] = html.escape(message)  # Use original message, just escaped
            response = requests.post(url, data=data)
            result = response.json()
        
        results.append(result)
        
        # Small delay between chunks to avoid rate limiting
        if i < len(chunks) - 1:
            time.sleep(0.1)
    
    # Return the first result for backward compatibility
    # (or the last one if you want the final result)
    return results[0] if results else {"ok": False, "error": "No message sent"}

    
def get_telegram_file_url(file_id):
    """Get the download URL for a Telegram file using file_id"""
    try:
        # Get file info from Telegram
        url = f"https://api.telegram.org/bot{telegram_bot_token}/getFile"
        params = {'file_id': file_id}
        
        response = requests.get(url, params=params)
        result = response.json()
        
        if result.get('ok') and 'result' in result:
            file_path = result['result']['file_path']
            # Construct download URL
            download_url = f"https://api.telegram.org/file/bot{telegram_bot_token}/{file_path}"
            return download_url
        else:
            print(f"Failed to get file URL for {file_id}: {result}")
            return None
            
    except Exception as e:
        print(f"Error getting Telegram file URL: {e}")
        return None


def send_telegram_audio(chat_id, text):
    """Convert text to speech and send as audio to Telegram"""
    try:
        # Convert text to speech - this returns a file path
        audio_file_path = text_to_speech(text)
        
        if not audio_file_path:
            raise Exception("Failed to generate audio from text")
        
        # Telegram Bot URL for sending audio
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendAudio"
        
        try:
            # Read the audio file and send it to Telegram
            with open(audio_file_path, 'rb') as audio_file:
                files = {
                    'audio': ('audio.mp3', audio_file, 'audio/mpeg')
                }
                
                data = {
                    'chat_id': chat_id,
                    'caption': f"🎵 Audio message: {text[:100]}..." if len(text) > 100 else f"🎵 Audio message: {text}"
                }
                
                # Send POST request to Telegram Bot API
                response = requests.post(url, data=data, files=files)
                
        finally:
            # Clean up the audio file created by text_to_speech
            import os
            try:
                os.unlink(audio_file_path)
            except:
                pass
            
        return response.json()
        
    except Exception as e:
        print(f"Error sending Telegram audio: {e}")
        return {"ok": False, "error": str(e)}


def send_telegram_file(chat_id, file_data, filename, caption=None):
    """Send a file/document to Telegram"""
    try:
        # Telegram Bot URL for sending documents
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendDocument"
        
        # Prepare the files for upload
        files = {
            'document': (filename, file_data, 'application/octet-stream')
        }
        
        data = {
            'chat_id': chat_id
        }
        
        if caption:
            data['caption'] = caption
        
        # Send POST request to Telegram Bot API
        response = requests.post(url, data=data, files=files)
        
        return response.json()
        
    except Exception as e:
        print(f"Error sending Telegram file: {e}")
        return {"ok": False, "error": str(e)}


def send_telegram_photo(chat_id, image_data, caption=None):
    """Send a photo to Telegram"""
    try:
        # Telegram Bot URL for sending photos
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendPhoto"
        
        # Prepare the files for upload
        files = {
            'photo': ('image.jpg', image_data, 'image/jpeg')
        }
        
        data = {
            'chat_id': chat_id
        }
        
        if caption:
            data['caption'] = caption
        
        # Send POST request to Telegram Bot API
        response = requests.post(url, data=data, files=files)
        
        return response.json()
        
    except Exception as e:
        print(f"Error sending Telegram photo: {e}")
        return {"ok": False, "error": str(e)}


def send_telegram_message_with_retry(chat_id, message, max_retries=3):
    """Send a Telegram message with retry logic for rate limiting"""
    for attempt in range(max_retries):
        try:
            response = send_telegram_message(chat_id, message)
            
            # Check if rate limited
            if not response.get('ok') and 'retry_after' in response.get('description', '').lower():
                retry_after = response.get('parameters', {}).get('retry_after', 5)
                print(f"Rate limited, waiting {retry_after} seconds before retry {attempt + 1}")
                time.sleep(retry_after)
                continue
            
            return response
            
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Final attempt failed: {e}")
                return {"ok": False, "error": str(e)}
            else:
                print(f"Attempt {attempt + 1} failed, retrying: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
    
    return {"ok": False, "error": "Max retries exceeded"}