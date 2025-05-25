"""
Slack-specific messenger implementation

This module provides the Slack implementation of the MessageSender interface,
wrapping existing Slack functionality to maintain backward compatibility.
"""

import logging
from typing import Dict, Any, Optional

from .base import MessageSender

# Set up logging
logger = logging.getLogger(__name__)

# Import existing Slack functions
try:
    from slack_integration import send_slack_message, send_audio_to_slack, send_file_to_slack
except ImportError as e:
    logger.error(f"Failed to import Slack functions: {e}")
    # Define fallback functions to prevent import errors
    def send_slack_message(message, channel, ts=None):
        raise NotImplementedError("Slack integration not available")
    
    def send_audio_to_slack(text, chat_id=None, ts=None):
        raise NotImplementedError("Slack integration not available")
    
    def send_file_to_slack(file_data, filename, chat_id, ts=None):
        raise NotImplementedError("Slack integration not available")


class SlackMessenger(MessageSender):
    """
    Slack-specific implementation of the MessageSender interface.
    
    This class wraps existing Slack integration functions to provide
    a consistent interface while maintaining full backward compatibility.
    """
    
    def __init__(self):
        """Initialize the Slack messenger."""
        self.platform_name = 'slack'
        logger.info("SlackMessenger initialized")
    
    def send_text_message(self, chat_id: str, message: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a text message to a Slack channel or DM.
        
        Args:
            chat_id (str): Slack channel ID or user ID
            message (str): The message content
            thread_id (str, optional): Slack thread timestamp for threaded replies
            
        Returns:
            Dict[str, Any]: Response from Slack API
            
        Raises:
            Exception: If sending fails
        """
        try:
            # Validate inputs
            if not self.validate_chat_id(chat_id):
                raise ValueError("Invalid chat_id for Slack")
            
            if not message or not message.strip():
                raise ValueError("Message cannot be empty")
            
            # Use existing Slack function
            # send_slack_message(message, channel, ts=None)
            result = send_slack_message(message, chat_id, thread_id)
            
            logger.info(f"Sent text message to Slack channel {chat_id}")
            
            # Ensure result is in expected format
            if isinstance(result, dict):
                return result
            else:
                return {"success": True, "result": result}
                
        except Exception as e:
            logger.error(f"Failed to send Slack text message: {e}")
            return self.handle_error(e, "send_text_message")
    
    def send_audio_message(self, chat_id: str, text: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert text to speech and send as audio to Slack.
        
        Args:
            chat_id (str): Slack channel ID or user ID
            text (str): Text to convert to speech
            thread_id (str, optional): Slack thread timestamp for threaded replies
            
        Returns:
            Dict[str, Any]: Response from Slack API
            
        Raises:
            Exception: If sending fails
        """
        try:
            # Validate inputs
            if not self.validate_chat_id(chat_id):
                raise ValueError("Invalid chat_id for Slack")
            
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            # Use existing Slack function
            # send_audio_to_slack(text, chat_id=None, ts=None)
            result = send_audio_to_slack(text, chat_id, thread_id)
            
            logger.info(f"Sent audio message to Slack channel {chat_id}")
            
            # Ensure result is in expected format
            if isinstance(result, dict):
                return result
            else:
                return {"success": True, "result": result}
                
        except Exception as e:
            logger.error(f"Failed to send Slack audio message: {e}")
            return self.handle_error(e, "send_audio_message")
    
    def send_file_message(self, chat_id: str, file_data: bytes, filename: str,
                         thread_id: Optional[str] = None, caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a file to a Slack channel.
        
        Args:
            chat_id (str): Slack channel ID or user ID
            file_data (bytes): The file content
            filename (str): Name of the file
            thread_id (str, optional): Slack thread timestamp for threaded replies
            caption (str, optional): Caption for the file (not used in current Slack implementation)
            
        Returns:
            Dict[str, Any]: Response from Slack API
            
        Raises:
            Exception: If sending fails
        """
        try:
            # Validate inputs
            if not self.validate_chat_id(chat_id):
                raise ValueError("Invalid chat_id for Slack")
            
            if not file_data:
                raise ValueError("File data cannot be empty")
            
            if not filename or not filename.strip():
                raise ValueError("Filename cannot be empty")
            
            # Use existing Slack function
            # send_file_to_slack(file_data, filename, chat_id, ts=None)
            result = send_file_to_slack(file_data, filename, chat_id, thread_id)
            
            logger.info(f"Sent file {filename} to Slack channel {chat_id}")
            
            # Ensure result is in expected format
            if isinstance(result, dict):
                return result
            else:
                return {"success": True, "result": result}
                
        except Exception as e:
            logger.error(f"Failed to send Slack file: {e}")
            return self.handle_error(e, "send_file_message")
    
    def send_image_message(self, chat_id: str, image_data: bytes, filename: str,
                          thread_id: Optional[str] = None, caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Send an image to a Slack channel.
        
        For Slack, images are sent as files, so this method delegates to send_file_message.
        
        Args:
            chat_id (str): Slack channel ID or user ID
            image_data (bytes): The image content
            filename (str): Name of the image file
            thread_id (str, optional): Slack thread timestamp for threaded replies
            caption (str, optional): Caption for the image
            
        Returns:
            Dict[str, Any]: Response from Slack API
        """
        try:
            # For Slack, images are handled as files
            return self.send_file_message(chat_id, image_data, filename, thread_id, caption)
            
        except Exception as e:
            logger.error(f"Failed to send Slack image: {e}")
            return self.handle_error(e, "send_image_message")
    
    def supports_audio(self) -> bool:
        """
        Check if Slack supports audio messages.
        
        Returns:
            bool: True (Slack supports audio via text-to-speech)
        """
        return True
    
    def supports_files(self) -> bool:
        """
        Check if Slack supports file uploads.
        
        Returns:
            bool: True (Slack supports file uploads)
        """
        return True
    
    def supports_images(self) -> bool:
        """
        Check if Slack supports image uploads.
        
        Returns:
            bool: True (Slack supports image uploads as files)
        """
        return True
    
    def supports_threads(self) -> bool:
        """
        Check if Slack supports threaded conversations.
        
        Returns:
            bool: True (Slack supports threaded replies)
        """
        return True
    
    def get_platform_name(self) -> str:
        """
        Get the platform name.
        
        Returns:
            str: 'slack'
        """
        return self.platform_name
    
    def validate_chat_id(self, chat_id: str) -> bool:
        """
        Validate Slack chat ID format.
        
        Slack channel IDs typically start with 'C' for channels, 'D' for DMs,
        'G' for group chats, etc. User IDs start with 'U'.
        
        Args:
            chat_id (str): The chat ID to validate
            
        Returns:
            bool: True if valid Slack chat ID format, False otherwise
        """
        if not isinstance(chat_id, str) or len(chat_id.strip()) == 0:
            return False
        
        chat_id = chat_id.strip()
        
        # Basic Slack ID validation - should start with specific letters and be alphanumeric
        if len(chat_id) < 9:  # Slack IDs are typically 9+ characters
            return False
        
        # Check if it starts with valid Slack ID prefixes
        valid_prefixes = ['C', 'D', 'G', 'U', 'B', 'W']  # Channel, DM, Group, User, Bot, Workspace
        if not any(chat_id.startswith(prefix) for prefix in valid_prefixes):
            return False
        
        # Check if the rest is alphanumeric (Slack IDs are alphanumeric)
        if not chat_id[1:].isalnum():
            return False
        
        return True
    
    def format_message(self, message: str) -> str:
        """
        Format a message for Slack.
        
        This method can be extended to handle Slack-specific formatting
        such as converting markdown to Slack's mrkdwn format.
        
        Args:
            message (str): The raw message content
            
        Returns:
            str: The formatted message
        """
        # For now, return as-is since existing Slack functions handle formatting
        # In the future, this could handle markdown -> mrkdwn conversion
        return message
    
    def handle_error(self, error: Exception, operation: str) -> Dict[str, Any]:
        """
        Handle Slack-specific errors.
        
        Args:
            error (Exception): The error that occurred
            operation (str): The operation that failed
            
        Returns:
            Dict[str, Any]: Standardized error response
        """
        error_response = {
            'success': False,
            'error': str(error),
            'operation': operation,
            'platform': self.platform_name
        }
        
        # Add Slack-specific error handling if needed
        error_str = str(error).lower()
        if 'channel_not_found' in error_str:
            error_response['error_type'] = 'channel_not_found'
        elif 'not_in_channel' in error_str:
            error_response['error_type'] = 'not_in_channel'
        elif 'rate_limited' in error_str:
            error_response['error_type'] = 'rate_limited'
        else:
            error_response['error_type'] = 'unknown'
        
        return error_response