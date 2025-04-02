import os
import tempfile
import wave
import base64
from io import BytesIO
import requests
from config import client, slack_bot_token, image_bucket_name, docs_bucket_name
import datetime
import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed


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


def transcribe_speech_from_memory(audio_stream):
    # Reset the stream's position to the beginning
    audio_stream.seek(0)

    # Create a temporary file to store the audio content
    with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as tmp_file:
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


def process_url(url):
    try:
        audio_stream = download_audio_to_memory(url)
        transcription = transcribe_speech_from_memory(audio_stream)
        print(f"Success: Transcription completed for URL: {url}")
        return transcription
    except Exception as e:
        print(f"Failure: Could not process URL: {url}. Error: {str(e)}")
        return None


def transcribe_multiple_urls(urls):
    results = []
    print(f'Transcribing audio from: {urls}')
    with ThreadPoolExecutor() as executor:
        # Start download and transcription operations and execute them concurrently
        future_to_url = {executor.submit(process_url, url): url for url in urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results.append(future.result())
            except Exception as exc:
                print(f'{url} generated an exception: {exc}')
    print(results)
    return results


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