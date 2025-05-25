import os
import tempfile
import wave
import base64
import csv
import openpyxl
import PyPDF2
from io import BytesIO, StringIO
import requests
from config import client, slack_bot_token, image_bucket_name, docs_bucket_name
import datetime
import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed
from docx import Document
from urllib.parse import urlparse, unquote

# Import additional dependencies for file processing
try:
    from nlp_utils import rank_sentences, load_stopwords
except ImportError:
    def rank_sentences(text, stopwords, max_sentences=50):
        return text[:1000]  # Fallback
    def load_stopwords(language):
        return []

stopwords = load_stopwords('english')


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
        with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="shimmer",
            input=text
        ) as response:
            response.stream_to_file(tmp_file.name)
        tmp_file_path = tmp_file.name

    return tmp_file_path


def upload_image_to_s3(image_url, bucket_name):
    # Download the image   
    headers = {
        'Authorization': f'Bearer {slack_bot_token}',
        'Content-Type': 'image/x-www-form-urlencoded'
    }
    response = requests.get(image_url, headers=headers)   

    if response.status_code != 200:
        raise Exception('Failed to download image')
        
    # Get the image content  
    image_content = BytesIO(response.content)

    file_extension = os.path.splitext(image_url)[1]
    s3_object_name = f"Maria_{datetime.datetime.now(datetime.UTC).strftime('%Y%m%d%H%M%S')}{file_extension}"

    # Upload to S3
    s3_client = boto3.client('s3')
    s3_client.upload_fileobj(image_content, bucket_name, s3_object_name)

    # Construct the S3 URL    
    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_object_name}"
    return s3_url


def transcribe_speech_from_memory(audio_stream, audio_format='.m4a'):
    """
    Transcribe audio from memory stream with support for different formats
    
    Args:
        audio_stream: BytesIO stream containing audio data
        audio_format: File extension for the audio format (e.g., '.m4a', '.ogg', '.mp3')
    """
    # Reset the stream's position to the beginning
    audio_stream.seek(0)

    # Create a temporary file to store the audio content
    with tempfile.NamedTemporaryFile(suffix=audio_format, delete=False) as tmp_file:
        tmp_file.write(audio_stream.read())
        tmp_file_path = tmp_file.name

    # Open the temporary file for reading
    with open(tmp_file_path, 'rb') as audio_file:
        # Create a transcription using OpenAI's Whisper model
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

    # Remove the temporary file  
    os.remove(tmp_file_path)
    return response.text


def download_audio_to_memory(url):
    headers = {
        'Authorization': f'Bearer {slack_bot_token}',
        'Content-Type': 'audio/x-www-form-urlencoded'
    }    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception('Failed to download audio')
        
    audio_content = BytesIO(response.content)
    
    response.raise_for_status()
    return audio_content


def download_telegram_audio_to_memory(url):
    """
    Download audio from Telegram file URL (no authorization needed)
    """
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f'Failed to download Telegram audio: {response.status_code}')
        
    audio_content = BytesIO(response.content)
    return audio_content


def process_url(url, platform='slack'):
    try:
        if platform == 'telegram':
            audio_stream = download_telegram_audio_to_memory(url)
            # Telegram voice messages are typically in OGG format
            transcription = transcribe_speech_from_memory(audio_stream, audio_format='.ogg')
        else:
            audio_stream = download_audio_to_memory(url)
            # Slack audio files are typically in M4A format
            transcription = transcribe_speech_from_memory(audio_stream, audio_format='.m4a')
        print(f"Success: Transcription completed for URL: {url}")
        return transcription
    except Exception as e:
        print(f"Failure: Could not process URL: {url}. Error: {str(e)}")
        return None


def process_telegram_url(url):
    """Process Telegram audio URL specifically"""
    return process_url(url, platform='telegram')


def transcribe_multiple_urls(urls, platform='slack'):
    results = []
    print(f'Transcribing audio from {platform}: {urls}')
    with ThreadPoolExecutor() as executor:
        if platform == 'telegram':
            # Use Telegram-specific processing
            future_to_url = {executor.submit(process_telegram_url, url): url for url in urls}
        else:
            # Use Slack processing (original behavior)
            future_to_url = {executor.submit(process_url, url): url for url in urls}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results.append(future.result())
            except Exception as exc:
                print(f'{url} generated an exception: {exc}')
    print(results)
    return results


def download_and_read_file(url, content_type, platform='slack'):
    """Download and read file content with platform-specific handling"""
    if platform == 'telegram':
        # Telegram files don't need authorization headers
        headers = {}
    else:
        # Slack files need authorization
        headers = {
            'Authorization': f'Bearer {slack_bot_token}',
            'Content-Type': 'image/x-www-form-urlencoded'
        }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Extract the original file name and extension from the URL    
        parsed_url = urlparse(url)
        original_file_name = os.path.basename(unquote(parsed_url.path))
        _, file_extension = os.path.splitext(original_file_name)

        # Define the S3 bucket and folder where the file will be saved 
        bucket_name = docs_bucket_name
        folder_name = 'uploads'

        # Use the original file extension for the temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(response.content)
            tmp_file.seek(0)
            
            # Upload the file to S3 with the original file name    
            file_key = f"{folder_name}/{original_file_name}"
            s3_client = boto3.client('s3')
            s3_client.upload_file(tmp_file.name, bucket_name, file_key)

            if 'text/csv' in content_type:
                f = StringIO(response.text)
                reader = csv.reader(f)
                return '\n'.join([','.join(row) for row in reader])
            elif 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type:
                workbook = openpyxl.load_workbook(tmp_file.name)
                sheet = workbook.active
                return '\n'.join([','.join([str(cell.value) for cell in row]) for row in sheet.rows])
            elif 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
                doc = Document(tmp_file.name)
                content = '\n'.join([p.text for p in doc.paragraphs])
                summary = rank_sentences(content, stopwords, max_sentences=50)
                return summary
            elif 'application/pdf' in content_type:
                pdf_reader = PyPDF2.PdfReader(tmp_file.name)
                text = ' '.join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
                summary = rank_sentences(text, stopwords, max_sentences=50)
                return summary
            elif 'text/plain' in content_type:
                with open(tmp_file.name, 'r') as f:
                    content = f.read()
                return content
            else:
                return 'Unsupported file type'
    except Exception as e:
        return f'Error processing file: {e}'


def convert_to_wav_in_memory(m4a_data):
    """
    Converts in-memory M4A/MP4 audio data to WAV format.
    Assumes the input is raw PCM audio data.

    Args:
        m4a_data (bytes): Audio data from M4A/MP4.

    Returns:
        bytes: Converted WAV data in memory.

    Raises:
        ValueError: If the input audio data is invalid.
        RuntimeError: If WAV conversion fails.
    """
    # Create an in-memory buffer for the output WAV file
    wav_buffer = BytesIO()

    try:
        # Open the buffer as a WAV file for writing
        with wave.open(wav_buffer, "wb") as wav_file:
            # Set the required WAV parameters
            wav_file.setnchannels(2)  # Stereo
            wav_file.setsampwidth(2)  # 16-bit samples (2 bytes per sample)
            wav_file.setframerate(44100)  # 44.1 kHz sample rate

            # Write the raw PCM audio data to the WAV file
            wav_file.writeframes(m4a_data)

        # Return WAV data as bytes
        wav_buffer.seek(0)  # Rewind buffer to the beginning
        return wav_buffer.read()

    except wave.Error as e:
        raise ValueError("Invalid WAV data or parameters.") from e

    except Exception as e:
        raise RuntimeError("An error occurred during WAV conversion.") from e

    finally:
        wav_buffer.close()