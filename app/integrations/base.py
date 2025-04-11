"""
Base Integration Class

This module defines the base integration class that all platform integrations should extend.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseIntegration(ABC):
    """
    Base class for all e-commerce platform integrations.
    
    This abstract class defines the interface that all platform integrations
    must implement to provide consistent functionality.
    """
    
    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate with the platform using the provided credentials.
        
        Args:
            credentials: Dictionary containing authentication credentials
            
        Returns:
            True if authentication was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_product_details(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details about a specific product.
        
        Args:
            product_id: Platform-specific product ID
            
        Returns:
            Dictionary containing product details or None if not found
        """
        pass
    
    @abstractmethod
    def get_product_reviews(self, product_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get reviews for a specific product.
        
        Args:
            product_id: Platform-specific product ID
            limit: Maximum number of reviews to return
            offset: Number of reviews to skip
            
        Returns:
            List of review dictionaries
        """
        pass
    
    @abstractmethod
    def register_webhook(self, event_type: str, callback_url: str) -> Dict[str, Any]:
        """
        Register a webhook to receive notifications from the platform.
        
        Args:
            event_type: Type of event to subscribe to
            callback_url: URL to receive webhook notifications
            
        Returns:
            Dictionary containing webhook registration details
        """
        pass
    
    @abstractmethod
    def verify_webhook(self, headers: Dict[str, str], payload: Dict[str, Any]) -> bool:
        """
        Verify that a webhook request is authentic.
        
        Args:
            headers: HTTP headers from the webhook request
            payload: JSON payload from the webhook request
            
        Returns:
            True if the webhook is authentic, False otherwise
        """
        pass
    
    @abstractmethod
    def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a webhook notification.
        
        Args:
            payload: JSON payload from the webhook request
            
        Returns:
            Dictionary containing processing results
        """
        pass 