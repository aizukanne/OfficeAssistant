import os
import wave
import base64
import tempfile
import requests
import concurrent.futures
from typing import List, Optional, BinaryIO
from io import BytesIO

from ..core.config import SLACK_BOT_TOKEN
from ..core.error_handlers import APIError
from ..clients.openai_client import client

def download_audio_to_memory(url: str) -> BytesIO:
    """
    Download audio file from URL to memory.

    Args:
        url: URL of the audio file

    Returns:
        BytesIO object containing the audio data

    Raises:
        APIError: If download fails
    """
    headers = {
        'Authorization': f'Bearer {SLACK_BOT_TOKEN}',
        'Content-Type': 'audio/x-www-form-urlencoded'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Check response headers
        if not response.headers.get('Content-Type', '').startswith('audio/'):
            raise APIError(
                message="Invalid content type",
                status_code=400,
                details={"content_type": response.headers.get('Content-Type')}
            )
        
        audio_content = BytesIO(response.content)
        return audio_content
        
    except requests.exceptions.RequestException as e:
        raise APIError(
            message="Failed to download audio",
            status_code=500,
            details={"error": str(e)}
        )

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

def transcribe_multiple_urls(urls):
    results = []
    print(f'Transcribing audio from: {urls}')
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start download and transcription operations and execute them concurrently
        future_to_url = {executor.submit(process_url, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results.append(future.result())
            except Exception as exc:
                print(f'{url} generated an exception: {exc}')
    print(results)
    return results

def process_url(url: str) -> Optional[str]:
    """
    Process a single audio URL - download and transcribe.

    Args:
        url: URL of the audio file

    Returns:
        Transcription text or None if processing fails
    """
    try:
        audio_stream = download_audio_to_memory(url)
        transcription = transcribe_speech_from_memory(audio_stream)
        print(f"Success: Transcription completed for URL: {url}")
        return transcription
    except Exception as e:
        print(f"Failure: Could not process URL: {url}. Error: {str(e)}")
        return None

def convert_to_wav_in_memory(m4a_data: bytes) -> bytes:
    """
    Converts in-memory M4A/MP4 audio data to WAV format.
    Assumes the input is raw PCM audio data.

    Args:
        m4a_data: Audio data from M4A/MP4

    Returns:
        WAV format audio data

    Raises:
        ValueError: If the input audio data is invalid
        RuntimeError: If WAV conversion fails
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

def process_audio_file(
    file_path: str,
    output_format: str = "mp3",
    sample_rate: int = 44100,
    channels: int = 2
) -> str:
    """
    Process an audio file with specified parameters.

    Args:
        file_path: Path to the input audio file
        output_format: Desired output format
        sample_rate: Sample rate in Hz
        channels: Number of audio channels

    Returns:
        Path to the processed audio file

    Raises:
        FileNotFoundError: If input file not found
        RuntimeError: If processing fails
    """
    try:
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(
            suffix=f".{output_format}",
            delete=False
        ) as tmp_file:
            output_path = tmp_file.name

        # Open input file
        with wave.open(file_path, 'rb') as wav_in:
            # Open output file
            with wave.open(output_path, 'wb') as wav_out:
                # Set output parameters
                wav_out.setnchannels(channels)
                wav_out.setsampwidth(wav_in.getsampwidth())
                wav_out.setframerate(sample_rate)
                
                # Copy audio data
                wav_out.writeframes(wav_in.readframes(wav_in.getnframes()))

        return output_path

    except FileNotFoundError:
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error processing audio file: {str(e)}")

def encode_audio_base64(audio_data: bytes) -> str:
    """
    Encode audio data as base64 string.

    Args:
        audio_data: Raw audio data

    Returns:
        Base64 encoded string
    """
    try:
        return base64.b64encode(audio_data).decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"Error encoding audio data: {str(e)}")

def decode_audio_base64(base64_string: str) -> bytes:
    """
    Decode base64 string to audio data.

    Args:
        base64_string: Base64 encoded audio data

    Returns:
        Raw audio data

    Raises:
        ValueError: If input string is invalid
    """
    try:
        return base64.b64decode(base64_string)
    except Exception as e:
        raise ValueError(f"Invalid base64 string: {str(e)}")

def save_audio_to_file(
    audio_data: bytes,
    file_path: str,
    format: str = "wav",
    sample_rate: int = 44100,
    channels: int = 2
) -> None:
    """
    Save audio data to a file.

    Args:
        audio_data: Raw audio data
        file_path: Output file path
        format: Audio format
        sample_rate: Sample rate in Hz
        channels: Number of audio channels

    Raises:
        RuntimeError: If saving fails
    """
    try:
        with wave.open(file_path, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data)
    except Exception as e:
        raise RuntimeError(f"Error saving audio file: {str(e)}")

def process_multiple_audio_files(
    file_paths: List[str],
    output_format: str = "mp3"
) -> List[str]:
    """
    Process multiple audio files concurrently.

    Args:
        file_paths: List of input file paths
        output_format: Desired output format

    Returns:
        List of processed file paths
    """
    processed_files = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_path = {
            executor.submit(
                process_audio_file,
                path,
                output_format
            ): path for path in file_paths
        }
        
        for future in concurrent.futures.as_completed(future_to_path):
            path = future_to_path[future]
            try:
                processed_files.append(future.result())
            except Exception as e:
                print(f"Error processing {path}: {str(e)}")
                
    return processed_files