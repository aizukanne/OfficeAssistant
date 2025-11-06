import base64
import mimetypes
import os
import json
import requests
from typing import Dict, List, Any, Optional

api_key = "Your API Key"

def save_binary_file(file_name: str, data: bytes) -> str:
    """Save binary data to a file and return the file path."""
    try:
        with open(file_name, "wb") as f:
            f.write(data)
        print(f"File saved to: {file_name}")
        return file_name
    except Exception as e:
        print(f"Error saving file {file_name}: {str(e)}")
        return ""

def save_binary_file(file_name: str, data: bytes) -> str:
    """Save binary data to a file and return the file path."""
    try:
        with open(file_name, "wb") as f:
            f.write(data)
        print(f"File saved to: {file_name}")
        return file_name
    except Exception as e:
        print(f"Error saving file {file_name}: {str(e)}")
        return ""


def gemini_generate_content(
    prompt: str,
    output_directory: str = "./generated_files",
    file_name_prefix: str = "generated_content",
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash-image-preview"
) -> Dict[str, Any]:
    """
    Generate content using Google's Gemini API with support for both text and image outputs.
    
    This function can be used as a tool by LLMs to generate creative content including images.
    Uses requests library instead of the genai SDK.
    
    Args:
        prompt (str): The text prompt to send to Gemini
        output_directory (str): Directory to save generated files (default: "./generated_files")
        file_name_prefix (str): Prefix for generated file names (default: "generated_content")
        api_key (str, optional): Gemini API key. If None, uses GEMINI_API_KEY environment variable
        model (str): Gemini model to use (default: "gemini-2.5-flash-image-preview")
    
    Returns:
        Dict[str, Any]: Dictionary containing:
            - "success": bool indicating if the operation was successful
            - "text_content": str containing all text responses
            - "generated_files": list of file paths for saved images
            - "error": str containing error message if success is False
    """
    
    result = {
        "success": False,
        "text_content": "",
        "generated_files": [],
        "error": ""
    }
    
    try:
        # Get API key from parameter or environment
        if api_key is None:
            api_key = os.environ.get("GEMINI_API_KEY")
        
        if not api_key:
            result["error"] = "GEMINI_API_KEY not found in environment variables or provided as parameter"
            return result
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Prepare the API request
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        
        # Prepare the request payload
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "response_modalities": ["IMAGE", "TEXT"],
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 8192
            }
        }
        
        # Make the streaming request
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            stream=True,
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code != 200:
            result["error"] = f"API request failed with status {response.status_code}: {response.text}"
            return result
        
        # Process the streaming response
        file_index = 0
        text_parts = []
        
        for line in response.iter_lines():
            if not line:
                continue
                
            line = line.decode('utf-8').strip()
            
            # Skip empty lines and lines that don't contain JSON
            if not line or not line.startswith('data: '):
                continue
            
            # Remove 'data: ' prefix
            json_str = line[6:]
            
            try:
                chunk_data = json.loads(json_str)
            except json.JSONDecodeError:
                # Skip malformed JSON lines
                continue
            
            # Process the chunk
            if 'candidates' not in chunk_data or not chunk_data['candidates']:
                continue
            
            candidate = chunk_data['candidates'][0]
            
            if 'content' not in candidate or 'parts' not in candidate['content']:
                continue
            
            parts = candidate['content']['parts']
            
            for part in parts:
                # Handle inline data (images)
                if 'inlineData' in part:
                    inline_data = part['inlineData']
                    if 'data' in inline_data:
                        # Decode base64 data
                        try:
                            data_buffer = base64.b64decode(inline_data['data'])
                            mime_type = inline_data.get('mimeType', 'application/octet-stream')
                            file_extension = mimetypes.guess_extension(mime_type) or ".bin"
                            
                            file_name = os.path.join(
                                output_directory, 
                                f"{file_name_prefix}_{file_index}{file_extension}"
                            )
                            file_index += 1
                            
                            saved_file = save_binary_file(file_name, data_buffer)
                            if saved_file:
                                result["generated_files"].append(saved_file)
                        except Exception as e:
                            print(f"Error processing image data: {str(e)}")
                
                # Handle text data
                elif 'text' in part:
                    text_content = part['text']
                    text_parts.append(text_content)
                    print(text_content, end='', flush=True)
        
        # Combine all text content
        result["text_content"] = "".join(text_parts)
        result["success"] = True
        
        print(f"\n\nGeneration completed successfully!")
        print(f"Text content length: {len(result['text_content'])} characters")
        print(f"Files generated: {len(result['generated_files'])}")
        
    except requests.exceptions.Timeout:
        result["error"] = "Request timed out. The generation may have taken too long."
    except requests.exceptions.RequestException as e:
        result["error"] = f"Request error: {str(e)}"
    except Exception as e:
        result["error"] = f"Error during content generation: {str(e)}"
        print(f"Error: {result['error']}")
    
    return result


def gemini_generate_image(
    prompt: str,
    output_directory: str = "./generated_files",
    file_name_prefix: str = "generated_content",
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash-image-preview"
) -> Dict[str, Any]:
    """
    Non-streaming version of the Gemini content generation function.
    Simpler but doesn't provide real-time feedback.
    """
    
    result = {
        "success": False,
        "text_content": "",
        "generated_files": [],
        "error": ""
    }
    
    try:
        # Get API key from parameter or environment
        if api_key is None:
            api_key = os.environ.get("GEMINI_API_KEY")
        
        if not api_key:
            result["error"] = "GEMINI_API_KEY not found in environment variables or provided as parameter"
            return result
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Prepare the API request (non-streaming)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        
        # Prepare the request payload
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "response_modalities": ["IMAGE", "TEXT"],
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 8192
            }
        }
        
        # Make the request
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code != 200:
            result["error"] = f"API request failed with status {response.status_code}: {response.text}"
            return result
        
        response_data = response.json()
        
        # Process the response
        file_index = 0
        text_parts = []
        
        if 'candidates' in response_data and response_data['candidates']:
            candidate = response_data['candidates'][0]
            
            if 'content' in candidate and 'parts' in candidate['content']:
                parts = candidate['content']['parts']
                
                for part in parts:
                    # Handle inline data (images)
                    if 'inlineData' in part:
                        inline_data = part['inlineData']
                        if 'data' in inline_data:
                            # Decode base64 data
                            try:
                                data_buffer = base64.b64decode(inline_data['data'])
                                mime_type = inline_data.get('mimeType', 'application/octet-stream')
                                file_extension = mimetypes.guess_extension(mime_type) or ".bin"
                                
                                file_name = os.path.join(
                                    output_directory, 
                                    f"{file_name_prefix}_{file_index}{file_extension}"
                                )
                                file_index += 1
                                
                                saved_file = save_binary_file(file_name, data_buffer)
                                if saved_file:
                                    result["generated_files"].append(saved_file)
                            except Exception as e:
                                print(f"Error processing image data: {str(e)}")
                    
                    # Handle text data
                    elif 'text' in part:
                        text_content = part['text']
                        text_parts.append(text_content)
        
        # Combine all text content
        result["text_content"] = "".join(text_parts)
        result["success"] = True
        
        print(f"Generation completed successfully!")
        print(f"Text content length: {len(result['text_content'])} characters")
        print(f"Files generated: {len(result['generated_files'])}")
        
    except requests.exceptions.Timeout:
        result["error"] = "Request timed out. The generation may have taken too long."
    except requests.exceptions.RequestException as e:
        result["error"] = f"Request error: {str(e)}"
    except Exception as e:
        result["error"] = f"Error during content generation: {str(e)}"
        print(f"Error: {result['error']}")
    
    return result


def gemini_tool_schema() -> Dict[str, Any]:
    """
    Return the JSON schema for this tool to be used by LLMs.
    
    Returns:
        Dict[str, Any]: Tool schema in OpenAI function calling format
    """
    return {
        "type": "function",
        "function": {
            "name": "gemini_generate_content",
            "description": "Generate creative content including text and images using Google's Gemini API. Supports multimodal output generation using requests library.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The text prompt to send to Gemini for content generation"
                    },
                    "output_directory": {
                        "type": "string",
                        "description": "Directory to save generated files",
                        "default": "./generated_files"
                    },
                    "file_name_prefix": {
                        "type": "string", 
                        "description": "Prefix for generated file names",
                        "default": "generated_content"
                    },
                    "api_key": {
                        "type": "string",
                        "description": "Gemini API key (optional, uses GEMINI_API_KEY env var if not provided)"
                    },
                    "model": {
                        "type": "string",
                        "description": "Gemini model to use",
                        "default": "gemini-2.5-flash-image-preview"
                    }
                },
                "required": ["prompt"]
            }
        }
    }


# Example usage and testing
if __name__ == "__main__":
    print("Testing Gemini API with requests library")
    print("=" * 60)
    
    # Example: Non-streaming version
    print("\n" + "="*50)
    print("\nExample 2: Non-streaming generation")
    result2 = gemini_generate_image(
        prompt="Write a short story about a robot learning to paint.",
        output_directory="./test_output",
        file_name_prefix="robot_story",
        api_key = api_key
    )
    
    print("\n" + "="*50)
    print("Non-streaming Result:")
    print(f"Success: {result2['success']}")
    print(f"Text length: {len(result2['text_content'])}")
    print(f"Files generated: {len(result2['generated_files'])}")
    if result2['error']:
        print(f"Error: {result2['error']}")
    
    # Print tool schema for LLM integration
    print("\n" + "="*50)
    print("Tool Schema for LLM Integration:")
    print(json.dumps(gemini_tool_schema(), indent=2))