"""
Feedback API Routes for ShopSentiment

This module provides API endpoints for managing user feedback.
"""

from flask import Blueprint, request, jsonify, current_app, render_template
from flask_login import current_user, login_required
from datetime import datetime
from bson.objectid import ObjectId

from app.utils.mongodb import (
    insert_feedback, 
    find_feedback_by_id,
    find_feedback_by_entity,
    find_feedback_by_user,
    update_feedback,
    delete_feedback
)
from app.models import Feedback

# Create Blueprint
feedback_bp = Blueprint('feedback', __name__, url_prefix='/api/feedback')

@feedback_bp.route('/', methods=['POST'])
def create_feedback():
    """Create new feedback."""
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Validate required fields
        required_fields = ['entity_type', 'entity_id', 'rating']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        # Validate rating
        try:
            rating = float(data['rating'])
            if rating < 1 or rating > 5:
                return jsonify({'error': 'Rating must be between 1 and 5'}), 400
            data['rating'] = rating
        except ValueError:
            return jsonify({'error': 'Rating must be a number'}), 400
            
        # Add user ID if authenticated
        if current_user.is_authenticated:
            data['user_id'] = current_user.id
            
        # Add timestamps
        now = datetime.now()
        data['created_at'] = now
        data['updated_at'] = now
        
        # Add empty array for tags if not provided
        if 'tags' not in data:
            data['tags'] = []
            
        # Insert feedback into database
        feedback_id = insert_feedback(data)
        
        if not feedback_id:
            return jsonify({'error': 'Failed to create feedback'}), 500
            
        return jsonify({
            'message': 'Feedback created successfully',
            'feedback_id': feedback_id
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error creating feedback: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@feedback_bp.route('/<feedback_id>', methods=['GET'])
def get_feedback(feedback_id):
    """Get feedback by ID."""
    try:
        # Find feedback in database
        feedback_data = find_feedback_by_id(feedback_id)
        
        if not feedback_data:
            return jsonify({'error': 'Feedback not found'}), 404
            
        # Convert ObjectId to string for JSON serialization
        feedback_data['_id'] = str(feedback_data['_id'])
        if feedback_data.get('user_id'):
            feedback_data['user_id'] = str(feedback_data['user_id'])
            
        return jsonify(feedback_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting feedback: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@feedback_bp.route('/entity/<entity_type>/<entity_id>', methods=['GET'])
def get_entity_feedback(entity_type, entity_id):
    """Get feedback for a specific entity."""
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Find feedback in database
        feedback_list = find_feedback_by_entity(entity_type, entity_id, limit, offset)
        
        # Format feedback for JSON serialization
        result = []
        for feedback in feedback_list:
            feedback['_id'] = str(feedback['_id'])
            if feedback.get('user_id'):
                feedback['user_id'] = str(feedback['user_id'])
            result.append(feedback)
            
        return jsonify({
            'entity_type': entity_type,
            'entity_id': entity_id,
            'feedback': result,
            'count': len(result)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting entity feedback: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@feedback_bp.route('/user/me', methods=['GET'])
@login_required
def get_my_feedback():
    """Get feedback submitted by the current user."""
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Find feedback in database
        feedback_list = find_feedback_by_user(current_user.id, limit, offset)
        
        # Format feedback for JSON serialization
        result = []
        for feedback in feedback_list:
            feedback['_id'] = str(feedback['_id'])
            feedback['user_id'] = str(feedback['user_id'])
            result.append(feedback)
            
        return jsonify({
            'user_id': current_user.id,
            'feedback': result,
            'count': len(result)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting user feedback: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@feedback_bp.route('/<feedback_id>', methods=['PUT', 'PATCH'])
@login_required
def update_feedback_route(feedback_id):
    """Update existing feedback."""
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Find feedback in database
        feedback_data = find_feedback_by_id(feedback_id)
        
        if not feedback_data:
            return jsonify({'error': 'Feedback not found'}), 404
            
        # Check if user is authorized to update this feedback
        if feedback_data.get('user_id') and str(feedback_data['user_id']) != current_user.id:
            if not current_user.is_admin:
                return jsonify({'error': 'Unauthorized to update this feedback'}), 403
                
        # Validate rating if provided
        if 'rating' in data:
            try:
                rating = float(data['rating'])
                if rating < 1 or rating > 5:
                    return jsonify({'error': 'Rating must be between 1 and 5'}), 400
                data['rating'] = rating
            except ValueError:
                return jsonify({'error': 'Rating must be a number'}), 400
                
        # Update timestamps
        data['updated_at'] = datetime.now()
        
        # Update feedback in database
        success = update_feedback(feedback_id, data)
        
        if not success:
            return jsonify({'error': 'Failed to update feedback'}), 500
            
        return jsonify({
            'message': 'Feedback updated successfully',
            'feedback_id': feedback_id
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error updating feedback: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@feedback_bp.route('/<feedback_id>', methods=['DELETE'])
@login_required
def delete_feedback_route(feedback_id):
    """Delete feedback."""
    try:
        # Find feedback in database
        feedback_data = find_feedback_by_id(feedback_id)
        
        if not feedback_data:
            return jsonify({'error': 'Feedback not found'}), 404
            
        # Check if user is authorized to delete this feedback
        if feedback_data.get('user_id') and str(feedback_data['user_id']) != current_user.id:
            if not current_user.is_admin:
                return jsonify({'error': 'Unauthorized to delete this feedback'}), 403
                
        # Delete feedback from database
        success = delete_feedback(feedback_id)
        
        if not success:
            return jsonify({'error': 'Failed to delete feedback'}), 500
            
        return jsonify({
            'message': 'Feedback deleted successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error deleting feedback: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Add a route to render the feedback form
@feedback_bp.route('/form', methods=['GET'])
def feedback_form():
    """Render the feedback form."""
    entity_type = request.args.get('entity_type', 'app')
    entity_id = request.args.get('entity_id', 'general')
    return render_template('feedback_form.html', entity_type=entity_type, entity_id=entity_id)

@feedback_bp.route('/component/<entity_type>/<entity_id>', methods=['GET'])
def feedback_component(entity_type, entity_id):
    """Render the feedback component for embedding in other pages."""
    return render_template('components/feedback_display.html', entity_type=entity_type, entity_id=entity_id) 