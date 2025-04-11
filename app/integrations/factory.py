"""
Integration Factory

This module provides a factory pattern for creating platform integrations.
"""

import logging
from typing import Dict, Any, Optional

from app.integrations.base import BaseIntegration
from app.integrations.amazon import AmazonIntegration

# Configure logging
logger = logging.getLogger(__name__)

# Registry of available integrations
INTEGRATIONS = {
    'amazon': AmazonIntegration
}

def get_integration(platform: str, credentials: Optional[Dict[str, Any]] = None) -> Optional[BaseIntegration]:
    """
    Get an integration instance for the specified platform.
    
    Args:
        platform: Platform name (e.g., 'amazon')
        credentials: Optional credentials for authentication
        
    Returns:
        Integration instance or None if platform is not supported
    """
    try:
        # Check if the platform is supported
        if platform not in INTEGRATIONS:
            logger.error(f"Platform '{platform}' is not supported")
            return None
        
        # Create integration instance
        integration_class = INTEGRATIONS[platform]
        integration = integration_class()
        
        # Authenticate if credentials are provided
        if credentials:
            success = integration.authenticate(credentials)
            if not success:
                logger.error(f"Authentication failed for {platform} integration")
                return None
        
        return integration
        
    except Exception as e:
        logger.error(f"Error creating integration for {platform}: {e}")
        return None

def register_integration(platform: str, integration_class: type) -> bool:
    """
    Register a new integration type.
    
    Args:
        platform: Platform name
        integration_class: Integration class
        
    Returns:
        True if registration was successful, False otherwise
    """
    try:
        # Ensure the class extends BaseIntegration
        if not issubclass(integration_class, BaseIntegration):
            logger.error(f"Integration class for {platform} does not extend BaseIntegration")
            return False
        
        # Register the integration
        INTEGRATIONS[platform] = integration_class
        logger.info(f"Successfully registered {platform} integration")
        
        return True
        
    except Exception as e:
        logger.error(f"Error registering integration for {platform}: {e}")
        return False

def list_integrations() -> Dict[str, type]:
    """
    Get a list of available integrations.
    
    Returns:
        Dictionary of platform names to integration classes
    """
    return INTEGRATIONS.copy() 