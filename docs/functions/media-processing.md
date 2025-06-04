# Media Processing

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [← Slack Integration](slack-integration.md) | [ERP Integrations →](erp-integrations.md)

The media processing module in `media_processing.py` handles various multimedia operations, including audio processing, image handling, and document conversion.

## Overview

The media processing module is responsible for:

- Converting text to speech
- Transcribing speech to text
- Processing audio files
- Handling image uploads
- Converting between media formats

## Audio Operations

### Text to Speech

```python
def text_to_speech(text, file_suffix=".mp3")
```

This function converts text to speech:

**Parameters:**
- `text`: The text to convert to speech
- `file_suffix`: (Optional) The file extension for the output file (default: ".mp3")

**Returns:**
- The path to the generated audio file

**Example:**
```python
audio_file = text_to_speech("Hello, this is a test message.")
```

**Example Usage:**

```
User: Can you convert this message to audio?
Maria: I've converted your message to audio and attached it here.
[Audio file attachment]
```

### Transcribe Speech from Memory

```python
def transcribe_speech_from_memory(audio_stream)
```

This function transcribes speech from an audio stream:

**Parameters:**
- `audio_stream`: The audio data as a binary stream

**Returns:**
- The transcribed text

**Example:**
```python
transcription = transcribe_speech_from_memory(audio_data)
```

**Example Usage:**

```
User: [Sends audio message]
Maria: I've transcribed your audio message: "Please schedule a meeting with the team for tomorrow at 2 PM to discuss the project timeline."
```

### Download Audio to Memory

```python
def download_audio_to_memory(url)
```

This function downloads audio from a URL to memory:

**Parameters:**
- `url`: The URL of the audio file

**Returns:**
- The audio data as a binary stream

**Example:**
```python
audio_data = download_audio_to_memory("https://example.com/audio.mp3")
```

### Process URL

```python
def process_url(url)
```

This function processes an audio URL:

**Parameters:**
- `url`: The URL of the audio file

**Returns:**
- The transcribed text

**Example:**
```python
transcription = process_url("https://example.com/audio.mp3")
```

### Transcribe Multiple URLs

```python
def transcribe_multiple_urls(urls)
```

This function transcribes multiple audio URLs:

**Parameters:**
- `urls`: A list of audio file URLs

**Returns:**
- A list of transcriptions

**Example:**
```python
transcriptions = transcribe_multiple_urls(["https://example.com/audio1.mp3", "https://example.com/audio2.mp3"])
```

### Convert to WAV in Memory

```python
def convert_to_wav_in_memory(m4a_data)
```

This function converts M4A audio data to WAV format in memory:

**Parameters:**
- `m4a_data`: The M4A audio data as a binary stream

**Returns:**
- The WAV audio data as a binary stream

**Example:**
```python
wav_data = convert_to_wav_in_memory(m4a_data)
```

## Image Operations

### Upload Image to S3

```python
def upload_image_to_s3(image_url, bucket_name)
```

This function uploads an image to S3:

**Parameters:**
- `image_url`: The URL of the image
- `bucket_name`: The name of the S3 bucket

**Returns:**
- The S3 URL of the uploaded image

**Example:**
```python
s3_url = upload_image_to_s3("https://example.com/image.jpg", "my-bucket")
```

**Example Usage:**

```
User: [Sends image]
Maria: I've processed the image you sent. It appears to be a diagram of the project architecture.
```

## Implementation Details

### Text to Speech Implementation

```python
def text_to_speech(text, file_suffix=".mp3"):
    """Convert text to speech."""
    try:
        # Generate a unique filename
        filename = f"/tmp/{uuid.uuid4()}{file_suffix}"
        
        # Use AWS Polly or other TTS service
        response = polly_client.synthesize_speech(
            Text=text,
            OutputFormat="mp3",
            VoiceId="Joanna"
        )
        
        # Save the audio stream to a file
        with open(filename, "wb") as file:
            file.write(response["AudioStream"].read())
        
        return filename
    except Exception as e:
        logger.error(f"Error in text_to_speech: {str(e)}")
        return None
```

### Speech Transcription Implementation

```python
def transcribe_speech_from_memory(audio_stream):
    """Transcribe speech from an audio stream."""
    try:
        # Use OpenAI Whisper or other transcription service
        response = openai_client.audio.transcriptions.create(
            file=audio_stream,
            model="whisper-1"
        )
        
        return response.text
    except Exception as e:
        logger.error(f"Error in transcribe_speech_from_memory: {str(e)}")
        return None
```

### Audio Download Implementation

```python
def download_audio_to_memory(url):
    """Download audio from a URL to memory."""
    try:
        response = requests.get(url)
        
        if response.status_code != 200:
            logger.error(f"Error downloading audio: {response.status_code}")
            return None
        
        return io.BytesIO(response.content)
    except Exception as e:
        logger.error(f"Error in download_audio_to_memory: {str(e)}")
        return None
```

### Audio Format Conversion

```python
def convert_to_wav_in_memory(m4a_data):
    """Convert M4A audio data to WAV format in memory."""
    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_in:
            temp_in.write(m4a_data.getvalue())
            temp_in_name = temp_in.name
        
        temp_out_name = temp_in_name.replace('.m4a', '.wav')
        
        # Convert using ffmpeg
        subprocess.run([
            'ffmpeg', '-i', temp_in_name, 
            '-acodec', 'pcm_s16le', 
            '-ar', '16000', 
            '-ac', '1', 
            temp_out_name
        ], check=True)
        
        # Read the converted file
        with open(temp_out_name, 'rb') as temp_out:
            wav_data = io.BytesIO(temp_out.read())
        
        # Clean up temporary files
        os.unlink(temp_in_name)
        os.unlink(temp_out_name)
        
        return wav_data
    except Exception as e:
        logger.error(f"Error in convert_to_wav_in_memory: {str(e)}")
        return None
```

### Image Upload Implementation

```python
def upload_image_to_s3(image_url, bucket_name):
    """Upload an image to S3."""
    try:
        # Download the image
        response = requests.get(image_url)
        
        if response.status_code != 200:
            logger.error(f"Error downloading image: {response.status_code}")
            return None
        
        # Generate a unique key
        key = f"images/{uuid.uuid4()}.jpg"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=response.content,
            ContentType=response.headers.get('Content-Type', 'image/jpeg')
        )
        
        # Return the S3 URL
        return f"https://{bucket_name}.s3.amazonaws.com/{key}"
    except Exception as e:
        logger.error(f"Error in upload_image_to_s3: {str(e)}")
        return None
```

## Media Processing Workflow

The typical media processing workflow follows these steps:

1. **Receive Media**: Receive media from Slack or other sources
2. **Identify Type**: Determine the media type (audio, image, etc.)
3. **Process Media**: Apply appropriate processing based on type
4. **Generate Response**: Create a response based on the processed media
5. **Deliver Result**: Send the result back to the user

## Best Practices

When working with media processing:

- Handle large files efficiently
- Implement proper error handling
- Consider format compatibility
- Optimize for performance
- Clean up temporary files
- Respect privacy and data protection
- Integrate with [Privacy Detection](privacy-detection.md) for PII scanning in media content

## Future Enhancements

Planned enhancements for media processing include:

- Enhanced audio quality options
- Additional voice options for text-to-speech
- Improved transcription accuracy
- Video processing capabilities
- Advanced image analysis
- Multi-language support

---

[← Back to Main](../README.md) | [← Functions Overview](README.md) | [← Slack Integration](slack-integration.md) | [ERP Integrations →](erp-integrations.md)