"""
Abstract base class for messaging platforms

This module defines the MessageSender interface that all platform-specific
messaging implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class MessageSender(ABC):
    """
    Abstract base class for platform-specific message senders.
    
    This class defines the common interface that all messaging platforms
    must implement to ensure consistent behavior across the application.
    """
    
    @abstractmethod
    def send_text_message(self, chat_id: str, message: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a text message to the specified chat.
        
        Args:
            chat_id (str): The chat/channel ID where the message should be sent
            message (str): The text content of the message
            thread_id (str, optional): Thread/message ID for threaded conversations
            
        Returns:
            Dict[str, Any]: Response from the messaging platform API
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass
    
    @abstractmethod
    def send_audio_message(self, chat_id: str, text: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert text to speech and send as an audio message.
        
        Args:
            chat_id (str): The chat/channel ID where the audio should be sent
            text (str): The text to convert to speech
            thread_id (str, optional): Thread/message ID for threaded conversations
            
        Returns:
            Dict[str, Any]: Response from the messaging platform API
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass
    
    @abstractmethod
    def send_file_message(self, chat_id: str, file_data: bytes, filename: str, 
                         thread_id: Optional[str] = None, caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a file/document to the specified chat.
        
        Args:
            chat_id (str): The chat/channel ID where the file should be sent
            file_data (bytes): The binary content of the file
            filename (str): The name of the file
            thread_id (str, optional): Thread/message ID for threaded conversations
            caption (str, optional): Caption/description for the file
            
        Returns:
            Dict[str, Any]: Response from the messaging platform API
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass
    
    @abstractmethod
    def send_image_message(self, chat_id: str, image_data: bytes, filename: str,
                          thread_id: Optional[str] = None, caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Send an image to the specified chat.
        
        Args:
            chat_id (str): The chat/channel ID where the image should be sent
            image_data (bytes): The binary content of the image
            filename (str): The name of the image file
            thread_id (str, optional): Thread/message ID for threaded conversations
            caption (str, optional): Caption/description for the image
            
        Returns:
            Dict[str, Any]: Response from the messaging platform API
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass
    
    @abstractmethod
    def supports_audio(self) -> bool:
        """
        Check if the platform supports audio messages.
        
        Returns:
            bool: True if audio messages are supported, False otherwise
        """
        pass
    
    @abstractmethod
    def supports_files(self) -> bool:
        """
        Check if the platform supports file uploads.
        
        Returns:
            bool: True if file uploads are supported, False otherwise
        """
        pass
    
    @abstractmethod
    def supports_images(self) -> bool:
        """
        Check if the platform supports image uploads.
        
        Returns:
            bool: True if image uploads are supported, False otherwise
        """
        pass
    
    @abstractmethod
    def supports_threads(self) -> bool:
        """
        Check if the platform supports threaded conversations.
        
        Returns:
            bool: True if threaded conversations are supported, False otherwise
        """
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Get the name of the messaging platform.
        
        Returns:
            str: The name of the platform (e.g., 'slack', 'telegram')
        """
        pass
    
    def validate_chat_id(self, chat_id: str) -> bool:
        """
        Validate if the chat ID is in the correct format for this platform.
        
        This is a default implementation that can be overridden by subclasses
        for platform-specific validation.
        
        Args:
            chat_id (str): The chat ID to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        return isinstance(chat_id, str) and len(chat_id.strip()) > 0
    
    def format_message(self, message: str) -> str:
        """
        Format a message for the specific platform.
        
        This is a default implementation that can be overridden by subclasses
        for platform-specific formatting (e.g., markdown conversion).
        
        Args:
            message (str): The raw message content
            
        Returns:
            str: The formatted message
        """
        return message
    
    def handle_error(self, error: Exception, operation: str) -> Dict[str, Any]:
        """
        Handle errors in a platform-specific way.
        
        This is a default implementation that can be overridden by subclasses.
        
        Args:
            error (Exception): The error that occurred
            operation (str): The operation that failed
            
        Returns:
            Dict[str, Any]: Error response in a standardized format
        """
        return {
            'success': False,
            'error': str(error),
            'operation': operation,
            'platform': self.get_platform_name()
        }