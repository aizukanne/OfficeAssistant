from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple

class ServiceInterface(ABC):
    """Base interface for all services."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the service."""
        pass
    
    @abstractmethod
    def validate_config(self) -> Dict[str, str]:
        """
        Validate service configuration.
        
        Returns:
            Dict[str, str]: Dictionary of missing/invalid configuration items
        """
        pass

class ExternalServiceInterface(ServiceInterface):
    """Interface for external services."""
    
    @abstractmethod
    async def fetch_content(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Fetch content from a URL.
        
        Args:
            url: URL to fetch content from
            
        Returns:
            Tuple[Optional[str], Optional[str]]: Content and content type
        """
        pass
    
    @abstractmethod
    async def process_content(
        self,
        content: str,
        content_type: str,
        full_text: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Process fetched content.
        
        Args:
            content: Content to process
            content_type: Type of content
            full_text: Whether to return full text or summary
            
        Returns:
            List[Dict[str, Any]]: Processed content
        """
        pass
    
    @abstractmethod
    def search(
        self,
        query: str,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Search external resources.
        
        Args:
            query: Search query
            **kwargs: Additional search parameters
            
        Returns:
            List[Dict[str, Any]]: Search results
        """
        pass

class StorageServiceInterface(ServiceInterface):
    """Interface for storage services."""
    
    @abstractmethod
    def save(
        self,
        data: Dict[str, Any],
        **kwargs: Any
    ) -> bool:
        """
        Save data to storage.
        
        Args:
            data: Data to save
            **kwargs: Additional parameters
            
        Returns:
            bool: Success status
        """
        pass
    
    @abstractmethod
    def retrieve(
        self,
        identifier: str,
        **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from storage.
        
        Args:
            identifier: Data identifier
            **kwargs: Additional parameters
            
        Returns:
            Optional[Dict[str, Any]]: Retrieved data
        """
        pass
    
    @abstractmethod
    def delete(
        self,
        identifier: str,
        **kwargs: Any
    ) -> bool:
        """
        Delete data from storage.
        
        Args:
            identifier: Data identifier
            **kwargs: Additional parameters
            
        Returns:
            bool: Success status
        """
        pass
    
    @abstractmethod
    def list(
        self,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        List stored data.
        
        Args:
            **kwargs: Filter parameters
            
        Returns:
            List[Dict[str, Any]]: List of stored data
        """
        pass

class MessageServiceInterface(ServiceInterface):
    """Interface for message services."""
    
    @abstractmethod
    def send_message(
        self,
        message: str,
        recipient: str,
        **kwargs: Any
    ) -> bool:
        """
        Send a message.
        
        Args:
            message: Message content
            recipient: Message recipient
            **kwargs: Additional parameters
            
        Returns:
            bool: Success status
        """
        pass
    
    @abstractmethod
    def get_messages(
        self,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Get messages.
        
        Args:
            **kwargs: Filter parameters
            
        Returns:
            List[Dict[str, Any]]: List of messages
        """
        pass

class AIServiceInterface(ServiceInterface):
    """Interface for AI services."""
    
    @abstractmethod
    def generate_content(
        self,
        prompt: str,
        **kwargs: Any
    ) -> str:
        """
        Generate content using AI.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
            
        Returns:
            str: Generated content
        """
        pass
    
    @abstractmethod
    def analyze_content(
        self,
        content: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Analyze content using AI.
        
        Args:
            content: Content to analyze
            **kwargs: Additional parameters
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        pass

class ServiceFactory:
    """Factory for creating service instances."""
    
    @staticmethod
    def create_service(service_type: str, **kwargs: Any) -> ServiceInterface:
        """
        Create a service instance.
        
        Args:
            service_type: Type of service to create
            **kwargs: Service configuration parameters
            
        Returns:
            ServiceInterface: Service instance
            
        Raises:
            ValueError: If service type is invalid
        """
        if service_type == "external":
            from .external_services import ExternalService
            return ExternalService(**kwargs)
        elif service_type == "storage":
            from .storage_service import StorageService
            return StorageService(**kwargs)
        elif service_type == "message":
            from .slack_service import SlackService
            return SlackService(**kwargs)
        elif service_type == "ai":
            from .openai_service import OpenAIService
            return OpenAIService(**kwargs)
        else:
            raise ValueError(f"Invalid service type: {service_type}")