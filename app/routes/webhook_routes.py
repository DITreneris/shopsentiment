"""
Webhook Routes for E-commerce Platform Integrations

This module provides API endpoints for handling webhooks from integrated platforms.
"""

import logging
from flask import Blueprint, request, jsonify, current_app, abort
import json

from app.integrations.factory import get_integration

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint
webhook_bp = Blueprint('webhook', __name__, url_prefix='/api/webhook')

@webhook_bp.route('/<platform>', methods=['POST'])
def handle_webhook(platform):
    """
    Handle webhook notifications from integrated platforms.
    
    Args:
        platform: Platform name (e.g., 'amazon')
    """
    try:
        # Get request data
        headers = request.headers
        payload = request.get_json()
        
        if not payload:
            logger.error(f"No payload received for {platform} webhook")
            return jsonify({"error": "No payload received"}), 400
        
        # Log webhook received
        logger.info(f"Received webhook from {platform}")
        
        # Get integration for the platform
        integration = get_integration(platform)
        if not integration:
            logger.error(f"Unsupported platform: {platform}")
            return jsonify({"error": f"Unsupported platform: {platform}"}), 400
        
        # Verify webhook signature
        if not integration.verify_webhook(headers, payload):
            logger.error(f"Invalid webhook signature for {platform}")
            return jsonify({"error": "Invalid webhook signature"}), 401
        
        # Process the webhook
        result = integration.process_webhook(payload)
        
        # Return the processing result
        return jsonify(result), 200 if result.get('success', False) else 400
        
    except Exception as e:
        logger.error(f"Error handling webhook from {platform}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@webhook_bp.route('/register/<platform>', methods=['POST'])
def register_webhook(platform):
    """
    Register a webhook with an integrated platform.
    
    Args:
        platform: Platform name (e.g., 'amazon')
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract required parameters
        event_type = data.get('event_type')
        callback_url = data.get('callback_url')
        credentials = data.get('credentials', {})
        
        if not event_type or not callback_url:
            return jsonify({"error": "Missing required parameters: event_type, callback_url"}), 400
        
        # Get integration for the platform
        integration = get_integration(platform, credentials)
        if not integration:
            return jsonify({"error": f"Failed to initialize {platform} integration"}), 400
        
        # Register the webhook
        result = integration.register_webhook(event_type, callback_url)
        
        # Return the registration result
        return jsonify(result), 201 if result.get('success', False) else 400
        
    except Exception as e:
        logger.error(f"Error registering webhook with {platform}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@webhook_bp.route('/status', methods=['GET'])
def webhook_status():
    """
    Get the status of available webhook integrations.
    
    Returns:
        JSON response with integration status
    """
    from app.integrations.factory import list_integrations
    
    # Get available integrations
    integrations = list_integrations()
    
    # Format response
    result = {
        "available_integrations": list(integrations.keys()),
        "total_integrations": len(integrations)
    }
    
    return jsonify(result), 200 