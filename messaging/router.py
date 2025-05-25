"""
Central message router for dispatching messages to appropriate platforms

This module contains the MessageRouter class that serves as the central
dispatcher for all messaging operations across different platforms.
"""

import logging
from typing import Dict, Any, Optional, Union
from .base import MessageSender

# Set up logging
logger = logging.getLogger(__name__)


class MessageRouter:
    """
    Central router for dispatching messages to platform-specific messengers.
    
    This class maintains a registry of available messaging platforms and
    routes all messaging operations to the appropriate platform-specific
    implementation based on the source parameter.
    """
    
    def __init__(self):
        """Initialize the message router with an empty messenger registry."""
        self._messengers: Dict[str, MessageSender] = {}
        self._initialized = False
    
    def register_messenger(self, platform: str, messenger: MessageSender) -> None:
        """
        Register a messenger for a specific platform.
        
        Args:
            platform (str): The platform identifier (e.g., 'slack', 'telegram')
            messenger (MessageSender): The messenger instance for this platform
            
        Raises:
            ValueError: If platform is empty or messenger is not a MessageSender instance
        """
        if not platform or not platform.strip():
            raise ValueError("Platform name cannot be empty")
        
        if not isinstance(messenger, MessageSender):
            raise ValueError("Messenger must be an instance of MessageSender")
        
        platform = platform.lower().strip()
        self._messengers[platform] = messenger
        logger.info(f"Registered messenger for platform: {platform}")
    
    def unregister_messenger(self, platform: str) -> bool:
        """
        Unregister a messenger for a specific platform.
        
        Args:
            platform (str): The platform identifier to unregister
            
        Returns:
            bool: True if messenger was unregistered, False if not found
        """
        platform = platform.lower().strip()
        if platform in self._messengers:
            del self._messengers[platform]
            logger.info(f"Unregistered messenger for platform: {platform}")
            return True
        return False
    
    def get_messenger(self, platform: str) -> Optional[MessageSender]:
        """
        Get the messenger for a specific platform.
        
        Args:
            platform (str): The platform identifier
            
        Returns:
            Optional[MessageSender]: The messenger instance, or None if not found
        """
        if not platform:
            return None
        
        platform = platform.lower().strip()
        return self._messengers.get(platform)
    
    def is_platform_supported(self, platform: str) -> bool:
        """
        Check if a platform is supported (has a registered messenger).
        
        Args:
            platform (str): The platform identifier to check
            
        Returns:
            bool: True if platform is supported, False otherwise
        """
        return self.get_messenger(platform) is not None
    
    def get_supported_platforms(self) -> list:
        """
        Get a list of all supported platforms.
        
        Returns:
            list: List of supported platform names
        """
        return list(self._messengers.keys())
    
    def initialize_default_messengers(self) -> None:
        """
        Initialize default messengers for Slack and Telegram.
        
        This method should be called after the router is created to set up
        the default platform messengers.
        """
        if self._initialized:
            return
        
        try:
            # Import here to avoid circular imports
            from .slack_messenger import SlackMessenger
            from .telegram_messenger import TelegramMessenger
            
            # Register default messengers
            self.register_messenger('slack', SlackMessenger())
            self.register_messenger('telegram', TelegramMessenger())
            
            self._initialized = True
            logger.info("Default messengers initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to initialize default messengers: {e}")
            raise
    
    def send_message(self, platform: str, chat_id: str, message: str, 
                    thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a text message via the specified platform.
        
        Args:
            platform (str): The platform to use for sending
            chat_id (str): The chat/channel ID
            message (str): The message content
            thread_id (str, optional): Thread ID for threaded conversations
            
        Returns:
            Dict[str, Any]: Response from the messaging platform
            
        Raises:
            ValueError: If platform is not supported or parameters are invalid
        """
        messenger = self.get_messenger(platform)
        if not messenger:
            error_msg = f"Platform '{platform}' is not supported. Available platforms: {self.get_supported_platforms()}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not chat_id or not message:
            raise ValueError("chat_id and message cannot be empty")
        
        try:
            logger.info(f"Sending text message to {platform} chat {chat_id}")
            return messenger.send_text_message(chat_id, message, thread_id)
        except Exception as e:
            logger.error(f"Failed to send message via {platform}: {e}")
            return messenger.handle_error(e, "send_text_message")
    
    def send_audio(self, platform: str, chat_id: str, text: str,
                  thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send an audio message via the specified platform.
        
        Args:
            platform (str): The platform to use for sending
            chat_id (str): The chat/channel ID
            text (str): The text to convert to speech
            thread_id (str, optional): Thread ID for threaded conversations
            
        Returns:
            Dict[str, Any]: Response from the messaging platform
            
        Raises:
            ValueError: If platform is not supported or doesn't support audio
        """
        messenger = self.get_messenger(platform)
        if not messenger:
            error_msg = f"Platform '{platform}' is not supported"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not messenger.supports_audio():
            error_msg = f"Platform '{platform}' does not support audio messages"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not chat_id or not text:
            raise ValueError("chat_id and text cannot be empty")
        
        try:
            logger.info(f"Sending audio message to {platform} chat {chat_id}")
            return messenger.send_audio_message(chat_id, text, thread_id)
        except Exception as e:
            logger.error(f"Failed to send audio via {platform}: {e}")
            return messenger.handle_error(e, "send_audio_message")
    
    def send_file(self, platform: str, chat_id: str, file_data: bytes, filename: str,
                 thread_id: Optional[str] = None, caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a file via the specified platform.
        
        Args:
            platform (str): The platform to use for sending
            chat_id (str): The chat/channel ID
            file_data (bytes): The file content
            filename (str): The file name
            thread_id (str, optional): Thread ID for threaded conversations
            caption (str, optional): File caption/description
            
        Returns:
            Dict[str, Any]: Response from the messaging platform
            
        Raises:
            ValueError: If platform is not supported or doesn't support files
        """
        messenger = self.get_messenger(platform)
        if not messenger:
            error_msg = f"Platform '{platform}' is not supported"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not messenger.supports_files():
            error_msg = f"Platform '{platform}' does not support file uploads"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not chat_id or not file_data or not filename:
            raise ValueError("chat_id, file_data, and filename cannot be empty")
        
        try:
            logger.info(f"Sending file {filename} to {platform} chat {chat_id}")
            return messenger.send_file_message(chat_id, file_data, filename, thread_id, caption)
        except Exception as e:
            logger.error(f"Failed to send file via {platform}: {e}")
            return messenger.handle_error(e, "send_file_message")
    
    def send_image(self, platform: str, chat_id: str, image_data: bytes, filename: str,
                  thread_id: Optional[str] = None, caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Send an image via the specified platform.
        
        Args:
            platform (str): The platform to use for sending
            chat_id (str): The chat/channel ID
            image_data (bytes): The image content
            filename (str): The image file name
            thread_id (str, optional): Thread ID for threaded conversations
            caption (str, optional): Image caption/description
            
        Returns:
            Dict[str, Any]: Response from the messaging platform
            
        Raises:
            ValueError: If platform is not supported or doesn't support images
        """
        messenger = self.get_messenger(platform)
        if not messenger:
            error_msg = f"Platform '{platform}' is not supported"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not messenger.supports_images():
            error_msg = f"Platform '{platform}' does not support image uploads"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not chat_id or not image_data or not filename:
            raise ValueError("chat_id, image_data, and filename cannot be empty")
        
        try:
            logger.info(f"Sending image {filename} to {platform} chat {chat_id}")
            return messenger.send_image_message(chat_id, image_data, filename, thread_id, caption)
        except Exception as e:
            logger.error(f"Failed to send image via {platform}: {e}")
            return messenger.handle_error(e, "send_image_message")
    
    def get_platform_capabilities(self, platform: str) -> Dict[str, bool]:
        """
        Get the capabilities of a specific platform.
        
        Args:
            platform (str): The platform to query
            
        Returns:
            Dict[str, bool]: Dictionary of platform capabilities
            
        Raises:
            ValueError: If platform is not supported
        """
        messenger = self.get_messenger(platform)
        if not messenger:
            raise ValueError(f"Platform '{platform}' is not supported")
        
        return {
            'audio': messenger.supports_audio(),
            'files': messenger.supports_files(),
            'images': messenger.supports_images(),
            'threads': messenger.supports_threads()
        }
    
    def __str__(self) -> str:
        """Return string representation of the router."""
        platforms = ', '.join(self.get_supported_platforms())
        return f"MessageRouter(platforms: [{platforms}])"
    
    def __repr__(self) -> str:
        """Return detailed string representation of the router."""
        return f"MessageRouter(messengers={list(self._messengers.keys())}, initialized={self._initialized})"


# Global router instance
_global_router = None


def get_global_router() -> MessageRouter:
    """
    Get the global message router instance.
    
    This function provides a singleton pattern for the message router,
    ensuring there's only one router instance throughout the application.
    
    Returns:
        MessageRouter: The global router instance
    """
    global _global_router
    if _global_router is None:
        _global_router = MessageRouter()
        _global_router.initialize_default_messengers()
    return _global_router


def reset_global_router() -> None:
    """
    Reset the global router instance.
    
    This function is primarily used for testing purposes to ensure
    a clean state between tests.
    """
    global _global_router
    _global_router = None