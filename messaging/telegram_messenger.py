"""
Telegram-specific messenger implementation

This module provides the Telegram implementation of the MessageSender interface,
including new functionality for audio and file messaging.
"""

import logging
from typing import Dict, Any, Optional

from .base import MessageSender

# Set up logging
logger = logging.getLogger(__name__)

# Import existing and new Telegram functions
try:
    from telegram_integration import (
        send_telegram_message, 
        send_telegram_audio, 
        send_telegram_file,
        send_telegram_photo
    )
except ImportError as e:
    logger.error(f"Failed to import Telegram functions: {e}")
    # Define fallback functions to prevent import errors
    def send_telegram_message(chat_id, message):
        raise NotImplementedError("Telegram integration not available")
    
    def send_telegram_audio(chat_id, text):
        raise NotImplementedError("Telegram audio integration not available")
    
    def send_telegram_file(chat_id, file_data, filename, caption=None):
        raise NotImplementedError("Telegram file integration not available")
    
    def send_telegram_photo(chat_id, image_data, caption=None):
        raise NotImplementedError("Telegram photo integration not available")


class TelegramMessenger(MessageSender):
    """
    Telegram-specific implementation of the MessageSender interface.
    
    This class provides full Telegram messaging capabilities including
    text, audio, file, and image messaging.
    """
    
    def __init__(self):
        """Initialize the Telegram messenger."""
        self.platform_name = 'telegram'
        logger.info("TelegramMessenger initialized")
    
    def send_text_message(self, chat_id: str, message: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a text message to a Telegram chat.
        
        Args:
            chat_id (str): Telegram chat ID
            message (str): The message content
            thread_id (str, optional): Not used in Telegram (no thread support)
            
        Returns:
            Dict[str, Any]: Response from Telegram API
            
        Raises:
            Exception: If sending fails
        """
        try:
            # Validate inputs
            if not self.validate_chat_id(chat_id):
                raise ValueError("Invalid chat_id for Telegram")
            
            if not message or not message.strip():
                raise ValueError("Message cannot be empty")
            
            # Log thread_id warning if provided (Telegram doesn't support threads)
            if thread_id:
                logger.warning("Telegram doesn't support threaded conversations. Ignoring thread_id.")
            
            # Format message for Telegram (convert to Telegram markdown if needed)
            formatted_message = self.format_message(message)
            
            # Use Telegram function
            result = send_telegram_message(chat_id, formatted_message)
            
            logger.info(f"Sent text message to Telegram chat {chat_id}")
            
            # Ensure result is in expected format
            if isinstance(result, dict):
                return result
            else:
                return {"success": True, "result": result}
                
        except Exception as e:
            logger.error(f"Failed to send Telegram text message: {e}")
            return self.handle_error(e, "send_text_message")
    
    def send_audio_message(self, chat_id: str, text: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert text to speech and send as audio to Telegram.
        
        Args:
            chat_id (str): Telegram chat ID
            text (str): Text to convert to speech
            thread_id (str, optional): Not used in Telegram (no thread support)
            
        Returns:
            Dict[str, Any]: Response from Telegram API
            
        Raises:
            Exception: If sending fails
        """
        try:
            # Validate inputs
            if not self.validate_chat_id(chat_id):
                raise ValueError("Invalid chat_id for Telegram")
            
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            # Log thread_id warning if provided
            if thread_id:
                logger.warning("Telegram doesn't support threaded conversations. Ignoring thread_id.")
            
            # Use Telegram audio function
            result = send_telegram_audio(chat_id, text)
            
            logger.info(f"Sent audio message to Telegram chat {chat_id}")
            
            # Ensure result is in expected format
            if isinstance(result, dict):
                return result
            else:
                return {"success": True, "result": result}
                
        except Exception as e:
            logger.error(f"Failed to send Telegram audio message: {e}")
            return self.handle_error(e, "send_audio_message")
    
    def send_file_message(self, chat_id: str, file_data: bytes, filename: str,
                         thread_id: Optional[str] = None, caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a file to a Telegram chat.
        
        Args:
            chat_id (str): Telegram chat ID
            file_data (bytes): The file content
            filename (str): Name of the file
            thread_id (str, optional): Not used in Telegram (no thread support)
            caption (str, optional): Caption for the file
            
        Returns:
            Dict[str, Any]: Response from Telegram API
            
        Raises:
            Exception: If sending fails
        """
        try:
            # Validate inputs
            if not self.validate_chat_id(chat_id):
                raise ValueError("Invalid chat_id for Telegram")
            
            if not file_data:
                raise ValueError("File data cannot be empty")
            
            if not filename or not filename.strip():
                raise ValueError("Filename cannot be empty")
            
            # Log thread_id warning if provided
            if thread_id:
                logger.warning("Telegram doesn't support threaded conversations. Ignoring thread_id.")
            
            # Use Telegram file function
            result = send_telegram_file(chat_id, file_data, filename, caption)
            
            logger.info(f"Sent file {filename} to Telegram chat {chat_id}")
            
            # Ensure result is in expected format
            if isinstance(result, dict):
                return result
            else:
                return {"success": True, "result": result}
                
        except Exception as e:
            logger.error(f"Failed to send Telegram file: {e}")
            return self.handle_error(e, "send_file_message")
    
    def send_image_message(self, chat_id: str, image_data: bytes, filename: str,
                          thread_id: Optional[str] = None, caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Send an image to a Telegram chat.
        
        Args:
            chat_id (str): Telegram chat ID
            image_data (bytes): The image content
            filename (str): Name of the image file
            thread_id (str, optional): Not used in Telegram (no thread support)
            caption (str, optional): Caption for the image
            
        Returns:
            Dict[str, Any]: Response from Telegram API
        """
        try:
            # Validate inputs
            if not self.validate_chat_id(chat_id):
                raise ValueError("Invalid chat_id for Telegram")
            
            if not image_data:
                raise ValueError("Image data cannot be empty")
            
            if not filename or not filename.strip():
                raise ValueError("Filename cannot be empty")
            
            # Log thread_id warning if provided
            if thread_id:
                logger.warning("Telegram doesn't support threaded conversations. Ignoring thread_id.")
            
            # Use Telegram photo function
            result = send_telegram_photo(chat_id, image_data, caption)
            
            logger.info(f"Sent image {filename} to Telegram chat {chat_id}")
            
            # Ensure result is in expected format
            if isinstance(result, dict):
                return result
            else:
                return {"success": True, "result": result}
                
        except Exception as e:
            logger.error(f"Failed to send Telegram image: {e}")
            return self.handle_error(e, "send_image_message")
    
    def supports_audio(self) -> bool:
        """
        Check if Telegram supports audio messages.
        
        Returns:
            bool: True (Telegram supports audio messages)
        """
        return True
    
    def supports_files(self) -> bool:
        """
        Check if Telegram supports file uploads.
        
        Returns:
            bool: True (Telegram supports file uploads)
        """
        return True
    
    def supports_images(self) -> bool:
        """
        Check if Telegram supports image uploads.
        
        Returns:
            bool: True (Telegram supports image uploads)
        """
        return True
    
    def supports_threads(self) -> bool:
        """
        Check if Telegram supports threaded conversations.
        
        Returns:
            bool: False (Telegram doesn't support threads like Slack)
        """
        return False
    
    def get_platform_name(self) -> str:
        """
        Get the platform name.
        
        Returns:
            str: 'telegram'
        """
        return self.platform_name
    
    def validate_chat_id(self, chat_id: str) -> bool:
        """
        Validate Telegram chat ID format.
        
        Telegram chat IDs can be:
        - Positive integers for private chats (user IDs)
        - Negative integers for group chats
        - Strings starting with '@' for usernames/channel names
        
        Args:
            chat_id (str): The chat ID to validate
            
        Returns:
            bool: True if valid Telegram chat ID format, False otherwise
        """
        if not isinstance(chat_id, str) or len(chat_id.strip()) == 0:
            return False
        
        chat_id = chat_id.strip()
        
        # Check for username format (starts with @)
        if chat_id.startswith('@'):
            return len(chat_id) > 1 and chat_id[1:].replace('_', '').isalnum()
        
        # Check for numeric chat ID (can be positive or negative)
        try:
            chat_id_int = int(chat_id)
            # Telegram user IDs are positive, group IDs are negative
            # Valid range is roughly -10^12 to 10^12
            return -10**12 <= chat_id_int <= 10**12
        except ValueError:
            return False
    
    def format_message(self, message: str) -> str:
        """
        Format a message for Telegram.
        
        This method converts common markdown to Telegram's supported markdown format.
        
        Args:
            message (str): The raw message content
            
        Returns:
            str: The formatted message for Telegram
        """
        if not message:
            return message
        
        # Telegram supports a subset of markdown
        # For now, we'll keep basic formatting and let Telegram handle it
        # Future enhancement: Convert from standard markdown to Telegram markdown
        
        # Basic conversions could include:
        # - **bold** -> *bold* (Telegram uses single asterisks for bold)
        # - __italic__ -> _italic_ (Telegram uses underscores for italic)
        # - `code` -> `code` (same)
        # - ```code``` -> ```code``` (same)
        
        formatted = message
        
        # Convert double asterisks to single for bold (if needed)
        # This is a simple implementation - a more robust one would use regex
        # formatted = formatted.replace('**', '*')
        
        return formatted
    
    def handle_error(self, error: Exception, operation: str) -> Dict[str, Any]:
        """
        Handle Telegram-specific errors.
        
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
        
        # Add Telegram-specific error handling
        error_str = str(error).lower()
        if 'chat not found' in error_str or 'bad request' in error_str:
            error_response['error_type'] = 'chat_not_found'
        elif 'forbidden' in error_str or 'bot was blocked' in error_str:
            error_response['error_type'] = 'bot_blocked'
        elif 'too many requests' in error_str or 'retry after' in error_str:
            error_response['error_type'] = 'rate_limited'
        elif 'file too large' in error_str:
            error_response['error_type'] = 'file_too_large'
        elif 'invalid file' in error_str:
            error_response['error_type'] = 'invalid_file'
        else:
            error_response['error_type'] = 'unknown'
        
        return error_response