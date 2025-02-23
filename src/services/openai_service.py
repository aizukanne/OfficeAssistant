import os
from typing import Dict, List, Any, Optional
import openai
from openai.error import OpenAIError

from src.config.settings import get_api_endpoint
from src.core.exceptions import (
    APIError,
    ValidationError,
    AuthenticationError,
    RateLimitError
)
from src.core.logging import ServiceLogger, log_function_call, log_error
from src.core.security import rate_limit, validate_request, audit_log
from src.core.performance import cached, monitor_performance
from src.interfaces import AIServiceInterface

class OpenAIService(AIServiceInterface):
    """Implementation of OpenAI service interface."""
    
    def __init__(self):
        """Initialize the service."""
        self.logger = ServiceLogger('openai_services')
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize OpenAI client."""
        try:
            openai.api_key = os.environ.get('OPENAI_API_KEY')
            self.validate_config()
        except Exception as e:
            self.logger.critical("Failed to initialize OpenAI client", error=str(e))
            raise AuthenticationError("Failed to initialize OpenAI client")
    
    def validate_config(self) -> Dict[str, str]:
        """Validate service configuration."""
        missing = {}
        
        if not os.environ.get('OPENAI_API_KEY'):
            missing['OPENAI_API_KEY'] = "OpenAI API key is required"
            
        return missing

    @log_function_call(logger)
    @log_error(logger)
    @rate_limit(tokens=1)
    @validate_request({
        'type': 'object',
        'properties': {
            'prompt': {'type': 'string'},
            'model': {'type': 'string'},
            'max_tokens': {'type': 'number'},
            'temperature': {'type': 'number'}
        },
        'required': ['prompt']
    })
    @audit_log('generate_content')
    @monitor_performance('openai_generate_content')
    def generate_content(
        self,
        prompt: str,
        **kwargs: Any
    ) -> str:
        """
        Generate content using OpenAI.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
            
        Returns:
            str: Generated content
            
        Raises:
            APIError: If API request fails
            ValidationError: If parameters are invalid
            RateLimitError: If rate limit is exceeded
        """
        try:
            # Validate input
            if not prompt.strip():
                raise ValidationError("Prompt cannot be empty")
            
            # Prepare parameters
            params = {
                'model': kwargs.get('model', 'gpt-4'),
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': kwargs.get('max_tokens', 2000),
                'temperature': kwargs.get('temperature', 0.7),
                'top_p': kwargs.get('top_p', 1.0),
                'frequency_penalty': kwargs.get('frequency_penalty', 0.0),
                'presence_penalty': kwargs.get('presence_penalty', 0.0)
            }
            
            # Make API request
            response = openai.ChatCompletion.create(**params)
            
            # Extract and return content
            return response.choices[0].message.content
            
        except openai.error.RateLimitError as e:
            self.logger.error("OpenAI rate limit exceeded", error=str(e))
            raise RateLimitError("OpenAI rate limit exceeded")
        except openai.error.APIError as e:
            self.logger.error("OpenAI API error", error=str(e))
            raise APIError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            self.logger.error("Error generating content", error=str(e))
            raise

    @log_function_call(logger)
    @log_error(logger)
    @rate_limit(tokens=1)
    @validate_request({
        'type': 'object',
        'properties': {
            'text': {'type': 'string'},
            'model': {'type': 'string'}
        },
        'required': ['text']
    })
    @monitor_performance('openai_get_embedding')
    def get_embedding(
        self,
        text: str,
        model: str = "text-embedding-ada-002"
    ) -> List[float]:
        """
        Get embedding for text.
        
        Args:
            text: Text to get embedding for
            model: Model to use
            
        Returns:
            List[float]: Embedding vector
        """
        try:
            response = openai.Embedding.create(
                model=model,
                input=text
            )
            return response['data'][0]['embedding']
            
        except openai.error.RateLimitError as e:
            self.logger.error("OpenAI rate limit exceeded", error=str(e))
            raise RateLimitError("OpenAI rate limit exceeded")
        except openai.error.APIError as e:
            self.logger.error("OpenAI API error", error=str(e))
            raise APIError(f"OpenAI API error: {str(e)}")

    @log_function_call(logger)
    @log_error(logger)
    @rate_limit(tokens=1)
    @validate_request({
        'type': 'object',
        'properties': {
            'content': {'type': 'string'},
            'model': {'type': 'string'}
        },
        'required': ['content']
    })
    @monitor_performance('openai_analyze_content')
    def analyze_content(
        self,
        content: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Analyze content using OpenAI.
        
        Args:
            content: Content to analyze
            **kwargs: Additional parameters
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            # Prepare system message for content analysis
            system_message = """
            Analyze the following content and provide:
            1. Main topics
            2. Sentiment
            3. Key entities
            4. Summary
            5. Language complexity score (1-10)
            """
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": content}
            ]
            
            response = openai.ChatCompletion.create(
                model=kwargs.get('model', 'gpt-4'),
                messages=messages,
                temperature=0.3  # Lower temperature for more focused analysis
            )
            
            # Parse response into structured format
            analysis = response.choices[0].message.content
            
            # Extract structured data (assuming response follows requested format)
            try:
                lines = analysis.split('\n')
                result = {
                    'topics': [],
                    'sentiment': '',
                    'entities': [],
                    'summary': '',
                    'complexity_score': 0
                }
                
                current_section = None
                for line in lines:
                    line = line.strip()
                    if 'Main topics' in line:
                        current_section = 'topics'
                    elif 'Sentiment' in line:
                        current_section = 'sentiment'
                    elif 'Key entities' in line:
                        current_section = 'entities'
                    elif 'Summary' in line:
                        current_section = 'summary'
                    elif 'Language complexity score' in line:
                        current_section = 'complexity'
                    elif line and current_section:
                        if current_section == 'topics':
                            result['topics'].append(line.lstrip('- '))
                        elif current_section == 'sentiment':
                            result['sentiment'] = line
                        elif current_section == 'entities':
                            result['entities'].append(line.lstrip('- '))
                        elif current_section == 'summary':
                            result['summary'] = line
                        elif current_section == 'complexity':
                            try:
                                score = int(line.split(':')[-1].strip())
                                result['complexity_score'] = score
                            except ValueError:
                                pass
                
                return result
                
            except Exception as e:
                self.logger.error("Error parsing analysis", error=str(e))
                return {'error': 'Failed to parse analysis', 'raw_response': analysis}
            
        except openai.error.RateLimitError as e:
            self.logger.error("OpenAI rate limit exceeded", error=str(e))
            raise RateLimitError("OpenAI rate limit exceeded")
        except openai.error.APIError as e:
            self.logger.error("OpenAI API error", error=str(e))
            raise APIError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            self.logger.error("Error analyzing content", error=str(e))
            raise

    @log_function_call(logger)
    @log_error(logger)
    @rate_limit(tokens=1)
    @validate_request({
        'type': 'object',
        'properties': {
            'prompt': {'type': 'string'},
            'n': {'type': 'number'},
            'size': {'type': 'string'}
        },
        'required': ['prompt']
    })
    @monitor_performance('openai_generate_image')
    def generate_image(
        self,
        prompt: str,
        n: int = 1,
        size: str = "1024x1024"
    ) -> List[str]:
        """
        Generate images using DALL-E.
        
        Args:
            prompt: Image description
            n: Number of images
            size: Image size
            
        Returns:
            List[str]: List of image URLs
        """
        try:
            response = openai.Image.create(
                prompt=prompt,
                n=n,
                size=size
            )
            
            return [item.url for item in response.data]
            
        except openai.error.RateLimitError as e:
            self.logger.error("OpenAI rate limit exceeded", error=str(e))
            raise RateLimitError("OpenAI rate limit exceeded")
        except openai.error.APIError as e:
            self.logger.error("OpenAI API error", error=str(e))
            raise APIError(f"OpenAI API error: {str(e)}")

    @log_function_call(logger)
    @log_error(logger)
    @cached(ttl=3600)  # Cache for 1 hour
    @monitor_performance('openai_list_models')
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List available OpenAI models.
        
        Returns:
            List[Dict[str, Any]]: List of models
        """
        try:
            response = openai.Model.list()
            return response.data
            
        except openai.error.APIError as e:
            self.logger.error("OpenAI API error", error=str(e))
            raise APIError(f"OpenAI API error: {str(e)}")

    @log_function_call(logger)
    @log_error(logger)
    @monitor_performance('openai_get_model')
    def get_model(self, model_id: str) -> Dict[str, Any]:
        """
        Get details of specific model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Dict[str, Any]: Model details
        """
        try:
            response = openai.Model.retrieve(model_id)
            return response
            
        except openai.error.APIError as e:
            self.logger.error("OpenAI API error", error=str(e))
            raise APIError(f"OpenAI API error: {str(e)}")