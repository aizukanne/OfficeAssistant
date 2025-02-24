"""Slack service implementation."""
import os
from typing import Dict, List, Optional, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from src.config.settings import get_api_endpoint
from src.core.exceptions import (
    APIError,
    ValidationError,
    AuthenticationError,
    SlackError,
    ConfigurationError
)
from src.utils.logging import log_message, log_error
from src.utils.decorators import log_function_call, log_error_decorator
from src.utils.error_handling import (
    handle_service_error,
    wrap_exceptions,
    retry_with_backoff
)
from src.interfaces import MessageServiceInterface
from src.services.storage import get_instance as get_storage_instance

class SlackService(MessageServiceInterface):
    """Implementation of Slack messaging service."""
    
    def __init__(self) -> None:
        """Initialize the service."""
        self.storage = get_storage_instance()
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize Slack client."""
        try:
            self.client = WebClient(token=os.environ.get('SLACK_BOT_TOKEN'))
            self.validate_config()
            log_message('INFO', 'slack', 'Service initialized')
        except Exception as e:
            handle_service_error(
                'slack',
                'initialize',
                ConfigurationError,
                token_exists=bool(os.environ.get('SLACK_BOT_TOKEN'))
            )(e)
    
    def validate_config(self) -> Dict[str, str]:
        """Validate service configuration."""
        missing = {}
        
        if not os.environ.get('SLACK_BOT_TOKEN'):
            missing['SLACK_BOT_TOKEN'] = "Slack bot token is required"
            log_message('ERROR', 'slack', 'Missing Slack bot token')
            
        return missing

    @log_function_call('slack')
    @wrap_exceptions(SlackError, operation='send_message')
    def send_message(
        self,
        message: str,
        recipient: str,
        **kwargs: Any
    ) -> bool:
        """
        Send a message to Slack.
        
        Args:
            message: Message content
            recipient: Channel or user ID
            **kwargs: Additional parameters
            
        Returns:
            bool: Success status
            
        Raises:
            SlackError: If message sending fails
            ValidationError: If parameters are invalid
        """
        try:
            # Validate input
            if not message.strip():
                raise ValidationError(
                    "Message cannot be empty",
                    message_length=len(message)
                )
            if not recipient.strip():
                raise ValidationError(
                    "Recipient cannot be empty",
                    recipient_length=len(recipient)
                )
            
            # Send message
            response = self.client.chat_postMessage(
                channel=recipient,
                text=message,
                thread_ts=kwargs.get('thread_ts'),
                mrkdwn=True
            )
            
            # Save to storage if successful
            if response['ok']:
                self.storage.save_message(
                    chat_id=recipient,
                    text=message,
                    role='assistant',
                    thread=kwargs.get('thread_ts')
                )
                log_message('INFO', 'slack', 'Message sent',
                          recipient=recipient, thread=kwargs.get('thread_ts'))
                return True
            
            raise SlackError(
                "Failed to send message",
                response_error=response.get('error', 'Unknown error')
            )
            
        except SlackApiError as e:
            handle_service_error(
                'slack',
                'send_message',
                SlackError,
                recipient=recipient,
                error_code=e.response.get('error')
            )(e)

    @log_function_call('slack')
    @retry_with_backoff(max_retries=3, exceptions=(SlackApiError,))
    @wrap_exceptions(SlackError, operation='send_file')
    def send_file(
        self,
        file_path: str,
        recipient: str,
        title: str,
        **kwargs: Any
    ) -> bool:
        """
        Send a file to Slack.
        
        Args:
            file_path: Path to file
            recipient: Channel or user ID
            title: File title
            **kwargs: Additional parameters
            
        Returns:
            bool: Success status
            
        Raises:
            SlackError: If file sending fails
            ValidationError: If parameters are invalid
        """
        try:
            if not file_path or not recipient or not title:
                raise ValidationError(
                    "Missing required parameters",
                    file_path=bool(file_path),
                    recipient=bool(recipient),
                    title=bool(title)
                )
            
            response = self.client.files_upload_v2(
                channel=recipient,
                file=file_path,
                title=title,
                thread_ts=kwargs.get('thread_ts')
            )
            
            if response['ok']:
                log_message('INFO', 'slack', 'File sent',
                          recipient=recipient, file=file_path)
                return True
                
            raise SlackError(
                "Failed to send file",
                response_error=response.get('error', 'Unknown error')
            )
            
        except SlackApiError as e:
            handle_service_error(
                'slack',
                'send_file',
                SlackError,
                recipient=recipient,
                file=file_path,
                error_code=e.response.get('error')
            )(e)

    @log_function_call('slack')
    @retry_with_backoff(max_retries=3, exceptions=(SlackApiError,))
    @wrap_exceptions(SlackError, operation='get_users')
    def get_users(self, user_id: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Get Slack users.
        
        Args:
            user_id: Optional specific user ID
            
        Returns:
            List[Dict[str, str]]: List of users
            
        Raises:
            SlackError: If user retrieval fails
        """
        try:
            if user_id:
                response = self.client.users_info(user=user_id)
                log_message('INFO', 'slack', 'Retrieved user info',
                          user_id=user_id)
                return [response['user']]
            
            response = self.client.users_list()
            log_message('INFO', 'slack', 'Retrieved users list',
                       count=len(response['members']))
            return response['members']
            
        except SlackApiError as e:
            handle_service_error(
                'slack',
                'get_users',
                SlackError,
                user_id=user_id,
                error_code=e.response.get('error')
            )(e)

    @log_function_call('slack')
    @retry_with_backoff(max_retries=3, exceptions=(SlackApiError,))
    @wrap_exceptions(SlackError, operation='get_channels')
    def get_channels(self, channel_id: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Get Slack channels.
        
        Args:
            channel_id: Optional specific channel ID
            
        Returns:
            List[Dict[str, str]]: List of channels
            
        Raises:
            SlackError: If channel retrieval fails
        """
        try:
            if channel_id:
                response = self.client.conversations_info(channel=channel_id)
                log_message('INFO', 'slack', 'Retrieved channel info',
                          channel_id=channel_id)
                return [response['channel']]
            
            response = self.client.conversations_list()
            log_message('INFO', 'slack', 'Retrieved channels list',
                       count=len(response['channels']))
            return response['channels']
            
        except SlackApiError as e:
            handle_service_error(
                'slack',
                'get_channels',
                SlackError,
                channel_id=channel_id,
                error_code=e.response.get('error')
            )(e)

    @log_function_call('slack')
    @retry_with_backoff(max_retries=3, exceptions=(SlackApiError,))
    @wrap_exceptions(SlackError, operation='search_messages')
    def search_messages(
        self,
        query: str,
        channel: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search Slack messages.
        
        Args:
            query: Search query
            channel: Optional channel to search in
            
        Returns:
            List[Dict[str, Any]]: Search results
            
        Raises:
            SlackError: If search fails
            ValidationError: If parameters are invalid
        """
        try:
            if not query:
                raise ValidationError(
                    "Search query cannot be empty",
                    query_length=len(query)
                )
            
            params = {'query': query}
            if channel:
                params['channel'] = channel
                
            response = self.client.search_messages(**params)
            matches = response['messages']['matches']
            log_message('INFO', 'slack', 'Messages searched',
                       query=query, channel=channel, matches=len(matches))
            return matches
            
        except SlackApiError as e:
            handle_service_error(
                'slack',
                'search_messages',
                SlackError,
                query=query,
                channel=channel,
                error_code=e.response.get('error')
            )(e)

    @log_function_call('slack')
    @wrap_exceptions(SlackError, operation='get_messages')
    def get_messages(
        self,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Get messages from storage.
        
        Args:
            **kwargs: Query parameters
            
        Returns:
            List[Dict[str, Any]]: List of messages
            
        Raises:
            SlackError: If retrieval fails
            ValidationError: If parameters are invalid
        """
        channel = kwargs.get('channel')
        limit = kwargs.get('limit', 100)
        
        if not channel:
            raise ValidationError(
                "Channel is required",
                provided_args=list(kwargs.keys())
            )
            
        log_message('INFO', 'slack', 'Getting messages from storage',
                   channel=channel, limit=limit)
        return self.storage.get_last_messages(
            chat_id=channel,
            num_messages=limit,
            table='assistant'
        )