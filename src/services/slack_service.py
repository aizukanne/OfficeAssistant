import json
from typing import Dict, List, Optional, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from src.config.settings import get_api_endpoint
from src.core.exceptions import (
    APIError,
    ValidationError,
    AuthenticationError
)
from src.core.logging import ServiceLogger, log_function_call, log_error
from src.core.security import rate_limit, validate_request, audit_log
from src.core.performance import cached, monitor_performance
from src.interfaces import MessageServiceInterface
from src.services import _storage_service

class SlackService(MessageServiceInterface):
    """Implementation of Slack messaging service."""
    
    def __init__(self):
        """Initialize the service."""
        self.logger = ServiceLogger('slack_services')
        self.storage = _storage_service
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize Slack client."""
        try:
            self.client = WebClient(token=os.environ.get('SLACK_BOT_TOKEN'))
            self.validate_config()
        except Exception as e:
            self.logger.critical("Failed to initialize Slack client", error=str(e))
            raise AuthenticationError("Failed to initialize Slack client")
    
    def validate_config(self) -> Dict[str, str]:
        """Validate service configuration."""
        missing = {}
        
        if not os.environ.get('SLACK_BOT_TOKEN'):
            missing['SLACK_BOT_TOKEN'] = "Slack bot token is required"
            
        return missing

    @log_function_call(logger)
    @log_error(logger)
    @rate_limit(tokens=1)
    @validate_request({
        'type': 'object',
        'properties': {
            'message': {'type': 'string'},
            'recipient': {'type': 'string'}
        },
        'required': ['message', 'recipient']
    })
    @audit_log('send_message')
    @monitor_performance('slack_send_message')
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
            APIError: If message sending fails
            ValidationError: If parameters are invalid
        """
        try:
            # Validate input
            if not message.strip():
                raise ValidationError("Message cannot be empty")
            if not recipient.strip():
                raise ValidationError("Recipient cannot be empty")
            
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
                return True
            
            raise APIError(f"Failed to send message: {response.get('error', 'Unknown error')}")
            
        except SlackApiError as e:
            self.logger.error("Slack API error", error=str(e))
            raise APIError(f"Slack API error: {str(e)}")
        except Exception as e:
            self.logger.error("Error sending message", error=str(e))
            raise

    @log_function_call(logger)
    @log_error(logger)
    @rate_limit(tokens=1)
    @validate_request({
        'type': 'object',
        'properties': {
            'file_path': {'type': 'string'},
            'recipient': {'type': 'string'},
            'title': {'type': 'string'}
        },
        'required': ['file_path', 'recipient', 'title']
    })
    @audit_log('send_file')
    @monitor_performance('slack_send_file')
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
        """
        try:
            response = self.client.files_upload_v2(
                channel=recipient,
                file=file_path,
                title=title,
                thread_ts=kwargs.get('thread_ts')
            )
            return response['ok']
            
        except SlackApiError as e:
            self.logger.error("Slack API error", error=str(e))
            raise APIError(f"Slack API error: {str(e)}")

    @log_function_call(logger)
    @log_error(logger)
    @cached(ttl=3600)  # Cache for 1 hour
    @monitor_performance('slack_get_users')
    def get_users(self, user_id: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Get Slack users.
        
        Args:
            user_id: Optional specific user ID
            
        Returns:
            List[Dict[str, str]]: List of users
        """
        try:
            if user_id:
                response = self.client.users_info(user=user_id)
                return [response['user']]
            
            response = self.client.users_list()
            return response['members']
            
        except SlackApiError as e:
            self.logger.error("Slack API error", error=str(e))
            raise APIError(f"Slack API error: {str(e)}")

    @log_function_call(logger)
    @log_error(logger)
    @cached(ttl=3600)  # Cache for 1 hour
    @monitor_performance('slack_get_channels')
    def get_channels(self, channel_id: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Get Slack channels.
        
        Args:
            channel_id: Optional specific channel ID
            
        Returns:
            List[Dict[str, str]]: List of channels
        """
        try:
            if channel_id:
                response = self.client.conversations_info(channel=channel_id)
                return [response['channel']]
            
            response = self.client.conversations_list()
            return response['channels']
            
        except SlackApiError as e:
            self.logger.error("Slack API error", error=str(e))
            raise APIError(f"Slack API error: {str(e)}")

    @log_function_call(logger)
    @log_error(logger)
    @rate_limit(tokens=1)
    @validate_request({
        'type': 'object',
        'properties': {
            'query': {'type': 'string'},
            'channel': {'type': 'string'}
        },
        'required': ['query']
    })
    @monitor_performance('slack_search_messages')
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
        """
        try:
            params = {'query': query}
            if channel:
                params['channel'] = channel
                
            response = self.client.search_messages(**params)
            return response['messages']['matches']
            
        except SlackApiError as e:
            self.logger.error("Slack API error", error=str(e))
            raise APIError(f"Slack API error: {str(e)}")

    @log_function_call(logger)
    @log_error(logger)
    def get_messages(
        self,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Get messages from storage."""
        channel = kwargs.get('channel')
        limit = kwargs.get('limit', 100)
        
        if not channel:
            raise ValidationError("Channel is required")
            
        return self.storage.get_last_messages(
            chat_id=channel,
            num_messages=limit,
            table='assistant'
        )