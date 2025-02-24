"""OpenAI service implementation."""
import os
from typing import Dict, List, Any, Optional
import openai
from openai.error import OpenAIError, RateLimitError as OpenAIRateLimitError

from src.config.settings import get_api_endpoint
from src.core.exceptions import (
    APIError,
    ValidationError,
    AuthenticationError,
    RateLimitError,
    OpenAIError,
    ConfigurationError
)
from src.utils.logging import log_message, log_error
from src.utils.decorators import log_function_call, log_error_decorator
from src.utils.error_handling import (
    handle_service_error,
    wrap_exceptions,
    retry_with_backoff
)
from src.interfaces import AIServiceInterface

class OpenAIService(AIServiceInterface):
    """Implementation of OpenAI service interface."""
    
    def __init__(self) -> None:
        """Initialize the service."""
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize OpenAI client."""
        try:
            openai.api_key = os.environ.get('OPENAI_API_KEY')
            self.validate_config()
            log_message('INFO', 'openai', 'Service initialized')
        except Exception as e:
            handle_service_error(
                'openai',
                'initialize',
                ConfigurationError,
                api_key_exists=bool(os.environ.get('OPENAI_API_KEY'))
            )(e)
    
    def validate_config(self) -> Dict[str, str]:
        """Validate service configuration."""
        missing = {}
        
        if not os.environ.get('OPENAI_API_KEY'):
            missing['OPENAI_API_KEY'] = "OpenAI API key is required"
            log_message('ERROR', 'openai', 'Missing OpenAI API key')
            
        return missing

    @log_function_call('openai')
    @retry_with_backoff(max_retries=3, exceptions=(OpenAIError,))
    @wrap_exceptions(OpenAIError, operation='generate_content')
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
            OpenAIError: If API request fails
            ValidationError: If parameters are invalid
            RateLimitError: If rate limit is exceeded
        """
        try:
            # Validate input
            if not prompt.strip():
                raise ValidationError(
                    "Prompt cannot be empty",
                    prompt_length=len(prompt)
                )
            
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
            
            log_message('INFO', 'openai', 'Generating content',
                       model=params['model'], max_tokens=params['max_tokens'])
            
            # Make API request
            response = openai.ChatCompletion.create(**params)
            
            # Extract and return content
            content = response.choices[0].message.content
            log_message('INFO', 'openai', 'Content generated',
                       length=len(content))
            return content
            
        except OpenAIRateLimitError as e:
            handle_service_error(
                'openai',
                'generate_content',
                RateLimitError,
                model=params['model']
            )(e)
        except OpenAIError as e:
            handle_service_error(
                'openai',
                'generate_content',
                OpenAIError,
                model=params['model']
            )(e)

    @log_function_call('openai')
    @retry_with_backoff(max_retries=3, exceptions=(OpenAIError,))
    @wrap_exceptions(OpenAIError, operation='get_embedding')
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
            
        Raises:
            OpenAIError: If API request fails
            ValidationError: If parameters are invalid
        """
        try:
            if not text.strip():
                raise ValidationError(
                    "Text cannot be empty",
                    text_length=len(text)
                )
            
            log_message('INFO', 'openai', 'Getting embedding',
                       model=model, text_length=len(text))
            
            response = openai.Embedding.create(
                model=model,
                input=text
            )
            
            embedding = response['data'][0]['embedding']
            log_message('INFO', 'openai', 'Embedding generated',
                       vector_size=len(embedding))
            return embedding
            
        except OpenAIRateLimitError as e:
            handle_service_error(
                'openai',
                'get_embedding',
                RateLimitError,
                model=model
            )(e)
        except OpenAIError as e:
            handle_service_error(
                'openai',
                'get_embedding',
                OpenAIError,
                model=model
            )(e)

    @log_function_call('openai')
    @retry_with_backoff(max_retries=3, exceptions=(OpenAIError,))
    @wrap_exceptions(OpenAIError, operation='analyze_content')
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
            
        Raises:
            OpenAIError: If API request fails
            ValidationError: If parameters are invalid
        """
        try:
            if not content.strip():
                raise ValidationError(
                    "Content cannot be empty",
                    content_length=len(content)
                )
            
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
            
            log_message('INFO', 'openai', 'Analyzing content',
                       content_length=len(content))
            
            response = openai.ChatCompletion.create(
                model=kwargs.get('model', 'gpt-4'),
                messages=messages,
                temperature=0.3  # Lower temperature for more focused analysis
            )
            
            # Parse response into structured format
            analysis = response.choices[0].message.content
            
            # Extract structured data
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
                
                log_message('INFO', 'openai', 'Content analyzed',
                           topics=len(result['topics']),
                           entities=len(result['entities']))
                return result
                
            except Exception as e:
                handle_service_error(
                    'openai',
                    'parse_analysis',
                    OpenAIError,
                    error_type='parsing_error'
                )(e)
            
        except OpenAIRateLimitError as e:
            handle_service_error(
                'openai',
                'analyze_content',
                RateLimitError,
                content_length=len(content)
            )(e)
        except OpenAIError as e:
            handle_service_error(
                'openai',
                'analyze_content',
                OpenAIError,
                content_length=len(content)
            )(e)

    @log_function_call('openai')
    @retry_with_backoff(max_retries=3, exceptions=(OpenAIError,))
    @wrap_exceptions(OpenAIError, operation='generate_image')
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
            
        Raises:
            OpenAIError: If API request fails
            ValidationError: If parameters are invalid
        """
        try:
            if not prompt.strip():
                raise ValidationError(
                    "Prompt cannot be empty",
                    prompt_length=len(prompt)
                )
            
            if n < 1 or n > 10:
                raise ValidationError(
                    "Number of images must be between 1 and 10",
                    requested=n
                )
            
            log_message('INFO', 'openai', 'Generating images',
                       count=n, size=size)
            
            response = openai.Image.create(
                prompt=prompt,
                n=n,
                size=size
            )
            
            urls = [item.url for item in response.data]
            log_message('INFO', 'openai', 'Images generated',
                       count=len(urls))
            return urls
            
        except OpenAIRateLimitError as e:
            handle_service_error(
                'openai',
                'generate_image',
                RateLimitError,
                count=n,
                size=size
            )(e)
        except OpenAIError as e:
            handle_service_error(
                'openai',
                'generate_image',
                OpenAIError,
                count=n,
                size=size
            )(e)

    @log_function_call('openai')
    @retry_with_backoff(max_retries=3, exceptions=(OpenAIError,))
    @wrap_exceptions(OpenAIError, operation='list_models')
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List available OpenAI models.
        
        Returns:
            List[Dict[str, Any]]: List of models
            
        Raises:
            OpenAIError: If API request fails
        """
        try:
            log_message('INFO', 'openai', 'Listing models')
            response = openai.Model.list()
            log_message('INFO', 'openai', 'Models listed',
                       count=len(response.data))
            return response.data
            
        except OpenAIError as e:
            handle_service_error(
                'openai',
                'list_models',
                OpenAIError
            )(e)

    @log_function_call('openai')
    @retry_with_backoff(max_retries=3, exceptions=(OpenAIError,))
    @wrap_exceptions(OpenAIError, operation='get_model')
    def get_model(self, model_id: str) -> Dict[str, Any]:
        """
        Get details of specific model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Dict[str, Any]: Model details
            
        Raises:
            OpenAIError: If API request fails
            ValidationError: If parameters are invalid
        """
        try:
            if not model_id:
                raise ValidationError("Model ID is required")
            
            log_message('INFO', 'openai', 'Getting model details',
                       model_id=model_id)
            response = openai.Model.retrieve(model_id)
            return response
            
        except OpenAIError as e:
            handle_service_error(
                'openai',
                'get_model',
                OpenAIError,
                model_id=model_id
            )(e)